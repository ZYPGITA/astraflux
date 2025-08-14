# -*- encoding: utf-8 -*-
import sys

__all__ = [
    "initialization_scheduler",
    "scheduler_add_job",
    "scheduler_remove_job",
    "scheduler_start",
    "scheduler_stop"
]


def initialization_scheduler(config: dict):
    """
    Initialize the scheduler.
    :param config: The configuration dictionary.
    """
    return sys.modules[__name__].initialization_scheduler(config)


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
    return sys.modules[__name__].scheduler_add_job(
        job_id, cron_str, func_object, timezone, args, kwargs, ipaddrs, exec_type)


def scheduler_remove_job(job_id):
    """
    Remove a job from the scheduler.
    :param job_id: The ID of the job to remove.
    """
    return sys.modules[__name__].scheduler_remove_job(job_id)


def scheduler_start():
    """
    Start the scheduler.
    """
    return sys.modules[__name__].scheduler_start()


def scheduler_stop():
    """
    Stop the scheduler.
    """
    return sys.modules[__name__].scheduler_stop()
