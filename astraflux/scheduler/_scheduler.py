# -*- encoding: utf-8 -*-

import time
import pytz
import pickle
import threading
import multiprocessing
from typing import Dict
from pymongo import MongoClient
from threading import Thread, Event
from datetime import datetime, timedelta

from astraflux.settings import *
from astraflux.interface import *
from .cronparser import CronParser


class Scheduler:
    _instance = None

    _db = None
    _jobs = None
    _locks = None
    _client = None
    _thread = None
    _running = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Scheduler, cls).__new__(cls)
            cls._instance.__initialize(*args, **kwargs)
        return cls._instance

    def __initialize(self, config: dict):
        self.logger = loguru(filename=KEY_PROJECT_NAME, task_id='scheduler')
        self.local_ip = get_ipaddr()
        self._client = MongoClient(config[MONGODB.KEY_MONGODB_URI])
        self._db = self._client[KEY_PROJECT_NAME]
        self._jobs = self._db.scheduled_jobs
        self._locks = self._db.job_locks
        self._running = Event()
        self._thread = None

        self.lock_refresh_interval = 5
        self.lock_expire_seconds = 10
        self.lock_refresh_threads: Dict[str, Event] = {}
        self.lock_thread_lock = threading.Lock()

    def start(self):
        self._running.set()
        self._thread = Thread(target=self._run_loop)
        self._thread.start()

    def stop(self):
        self._running.clear()
        if self._thread:
            self._thread.join()

        with self.lock_thread_lock:
            for job_id, stop_event in self.lock_refresh_threads.items():
                stop_event.set()
            self.lock_refresh_threads.clear()

    def _run_loop(self):
        while self._running.is_set():
            try:
                now = datetime.now(pytz.utc)
                due_jobs = self._jobs.find({
                    "enabled": True,
                    "next_run_time": {"$lte": now}
                })
                for job in due_jobs:
                    self._execute_job(job)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(5)

    def _execute_job(self, job):
        ipaddrs = job.get("ipaddrs", [])
        if ipaddrs and self.local_ip not in ipaddrs:
            self.logger.debug(f"Skip task {job['_id']}, the current IP {self.local_ip} is not in the execution list")
            return

        lock_expire = datetime.now(pytz.utc) + timedelta(seconds=self.lock_expire_seconds)
        lock_result = self._locks.update_one(
            {"job_id": job["_id"], "expire_at": {"$lt": datetime.now(pytz.utc)}},
            {"$set": {"expire_at": lock_expire}},
            upsert=True
        )

        if lock_result.modified_count > 0 or lock_result.upserted_id:
            try:
                func = pickle.loads(job["func"])
                exec_type = job.get("exec_type", "thread")

                self._start_lock_refresh(job["_id"])

                if exec_type == "process":
                    self.logger.debug(f"Starting process task: {job['_id']}")
                    process = multiprocessing.Process(
                        target=self._run_task,
                        args=(func, job["args"], job["kwargs"])
                    )
                    process.daemon = True
                    process.start()
                else:
                    self.logger.debug(f"Starting thread task: {job['_id']}")
                    thread = Thread(
                        target=self._run_task,
                        args=(func, job["args"], job["kwargs"])
                    )
                    thread.daemon = True
                    thread.start()

                cron_parser = CronParser(
                    cron_str=job["cron"],
                    timezone=job.get("timezone", "UTC")
                )
                next_run = cron_parser.get_next_run(datetime.now(pytz.utc))

                self._jobs.update_one(
                    {"_id": job["_id"]},
                    {"$set": {"next_run_time": next_run, "last_run_time": datetime.now(pytz.utc)}}
                )
            except Exception as e:
                self.logger.error(f"Task execution failed: {job['_id']} - {str(e)}")
                self._stop_lock_refresh(job["_id"])
                self._locks.delete_one({"job_id": job["_id"]})

    def _start_lock_refresh(self, job_id: str):
        stop_event = Event()

        refresh_thread = Thread(
            target=self._refresh_lock,
            args=(job_id, stop_event),
            daemon=True
        )
        refresh_thread.start()

        with self.lock_thread_lock:
            self.lock_refresh_threads[job_id] = stop_event

    def _stop_lock_refresh(self, job_id: str):
        with self.lock_thread_lock:
            stop_event = self.lock_refresh_threads.pop(job_id, None)
            if stop_event:
                stop_event.set()

    def _refresh_lock(self, job_id: str, stop_event: Event):
        while not stop_event.is_set():
            try:
                lock_expire = datetime.now(pytz.utc) + timedelta(seconds=self.lock_expire_seconds)
                self._locks.update_one(
                    {"job_id": job_id},
                    {"$set": {"expire_at": lock_expire}}
                )
                time.sleep(self.lock_refresh_interval)
            except Exception as e:
                self.logger.error(f"Failed to refresh lock for job {job_id}: {str(e)}")
                break

        try:
            self._locks.delete_one({"job_id": job_id})
        except Exception as e:
            self.logger.error(f"Failed to delete lock for job {job_id}: {str(e)}")

    @staticmethod
    def _run_task(func, args, kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            raise e

    def add_job(self, job_id, cron_str, func_object, timezone="UTC", args=None, kwargs=None, ipaddrs=None,
                exec_type="thread"):
        """
        Add a job to the scheduler.
        :param job_id: The ID of the job.
        :param cron_str: The cron string defining the schedule.
        :param func_object: The function object to execute.
        :param timezone: The timezone for the schedule.
        :param args: Additional arguments to pass to the function.
        :param kwargs: Additional keyword arguments to pass to the function.
        :param ipaddrs: List of allowed IP addresses to run the task.
        :param exec_type: The type of task to run. thread / process
        """

        existing_job = self._jobs.find_one({"_id": job_id})
        if existing_job:
            self.logger.warning(f"Job '{job_id}' already exists. Skipping insertion.")
            return

        cron_parser = CronParser(cron_str, timezone=timezone)
        next_run = cron_parser.get_next_run(datetime.now(pytz.utc))

        job_data = {
            "_id": job_id,
            "cron": cron_str,
            "func": pickle.dumps(func_object),
            "timezone": timezone,
            "args": args or [],
            "kwargs": kwargs or {},
            "enabled": True,
            "next_run_time": next_run,
            "last_run_time": None,
            "exec_type": exec_type
        }

        if ipaddrs is not None:
            job_data["ipaddrs"] = ipaddrs

        self._jobs.insert_one(job_data)

    def remove_job(self, job_id):
        """Remove a job from the scheduler."""
        self._jobs.delete_one({"_id": job_id})


def initialization_scheduler(config: dict):
    """
     Initialize the scheduler.
     :param config: The configuration dictionary.
    """
    Scheduler(config=config)


def scheduler_add_job(job_id, cron_str, func_object, timezone="UTC", args=None, kwargs=None, ipaddrs=None,
                      exec_type="thread"):
    """
    Add a job to the scheduler.
    :param job_id: The ID of the job.
    :param cron_str: The cron string defining the schedule.
    :param func_object: The function object to execute.
    :param timezone: The timezone for the schedule.
    :param args: Additional arguments to pass to the function.
    :param kwargs: Additional keyword arguments to pass to the function.
    :param ipaddrs: List of allowed IP addresses to run the task.
    :param exec_type: The type of task to run. thread / process
    """

    Scheduler().add_job(job_id, cron_str, func_object, timezone, args, kwargs, ipaddrs, exec_type)


def scheduler_remove_job(job_id):
    """
    Remove a job from the scheduler.
    :param job_id: The ID of the job to remove.
    """
    Scheduler().remove_job(job_id)


def scheduler_start():
    """
    Start the scheduler.
    """
    Scheduler().start()


def scheduler_stop():
    """
    Stop the scheduler.
    """
    Scheduler().stop()


def register():
    from astraflux.interface import scheduler
    scheduler.initialization_scheduler = initialization_scheduler
    scheduler.scheduler_add_job = scheduler_add_job
    scheduler.scheduler_remove_job = scheduler_remove_job
    scheduler.scheduler_start = scheduler_start
    scheduler.scheduler_stop = scheduler_stop

    import sys
    sys.modules['astraflux.interface.scheduler'] = scheduler
