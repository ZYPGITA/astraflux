# -*- encoding: utf-8 -*-

from astraflux.definitions.constants import *
from astraflux.interface.logger import get_logger
from astraflux.interface.rabbitmq import rabbitmq_send_message
from astraflux.interface.data_access import task_find_paginated, find_services, task_collector


class TaskScheduler:
    """
    Task Scheduler - Distributes tasks to worker nodes based on availability and priority

    This class manages the distribution of tasks from the main task queue to available
    worker nodes. It handles both main tasks and their subtasks, ensuring optimal
    resource utilization while maintaining task execution order and dependencies.
    """

    def __init__(self):
        """Initialize the Task Scheduler with logging capabilities"""
        self.logger = get_logger(filename=PROJECT_NAME, task_id='task_scheduler')

    def execute(self):
        """
        Execute the main task scheduling cycle

        Performs the complete task distribution workflow:
        1. Queries current worker capacity across all queues
        2. Cleans up failed/stopped tasks and their subtasks
        3. Schedules pending tasks based on priority and available capacity

        The scheduling follows a specific priority order:
        - Subtasks of completed main tasks are processed first
        - Main tasks in WAITING status are processed next
        """

        worker_capacity = self._get_worker_capacity()
        self.logger.info(f'Worker capacity: {worker_capacity}')

        self._cleanup_failed_tasks()

        self._schedule_pending_tasks(worker_capacity)

    @staticmethod
    def _get_worker_capacity():
        """
        Calculate available capacity for each worker queue

        Queries the service registry to determine:
        - Maximum processes each worker can handle
        - Currently running processes per worker
        - Available capacity (max - running) per worker queue

        Returns:
            dict: Mapping of queue names to available task slots
                  Example: {'queue1': 5, 'queue2': 3}
        """
        services = find_services(
            query={},
            fields={
                '_id': 0,
                DEFINITIONS.BUILD.WORKER_NAME: 1,
                DEFINITIONS.BUILD.WORKER_MAX_PROCESS: 1,
                DEFINITIONS.BUILD.WORKER_RUN_PROCESS: 1
            },
        )

        capacity = {}
        for service in services:
            worker_name = service[DEFINITIONS.BUILD.WORKER_NAME]
            max_processes = service[DEFINITIONS.BUILD.WORKER_MAX_PROCESS]
            running_processes = len(service[DEFINITIONS.BUILD.WORKER_RUN_PROCESS])

            capacity[worker_name] = capacity.get(worker_name, 0) + max_processes - running_processes

        return capacity

    @staticmethod
    def _cleanup_failed_tasks():
        """
        Clean up failed or stopped tasks and their subtasks

        This method handles task failure scenarios by:
        1. Identifying main tasks that have failed or been stopped
        2. Marking all subtasks of these failed main tasks as STOPPED
        3. Preventing orphaned subtasks from consuming resources

        Only processes non-subtasks (main tasks) that are in FAILED or STOPPED state
        """
        failed_main_tasks = task_find_paginated(
            query={
                DEFINITIONS.TASK.STATUS: {
                    '$in': [DEFINITIONS.STATUS.FAILED, DEFINITIONS.STATUS.STOPPED]
                },
                DEFINITIONS.TASK.IS_SUB_TASK: False
            },
            fields={DEFINITIONS.TASK.ID: 1},
            limit=1000,
            skip=0
        )[1]

        if failed_main_tasks:
            task_collector().update(
                query={
                    DEFINITIONS.TASK.SOURCE_ID: {
                        '$in': [task[DEFINITIONS.TASK.ID] for task in failed_main_tasks]
                    }
                },
                data={DEFINITIONS.TASK.STATUS: DEFINITIONS.STATUS.STOPPED}
            )

    def _schedule_pending_tasks(self, worker_capacity):
        """
        Schedule all pending tasks based on available capacity

        This method coordinates the scheduling of:
        - Main tasks that are waiting to execute
        - Subtasks of completed main tasks that haven't finished

        Args:
            worker_capacity (dict): Available capacity per worker queue

        Processing order:
        1. Subtasks of successfully completed main tasks (highest priority)
        2. Main tasks in WAITING status (normal priority)
        """

        main_tasks = task_find_paginated(
            query={
                DEFINITIONS.TASK.STATUS: {
                    '$in': [DEFINITIONS.STATUS.WAITING, DEFINITIONS.STATUS.SUCCESS]
                },
                DEFINITIONS.TASK.IS_SUB_TASK: False,
                DEFINITIONS.TASK.IS_SUB_TASK_ALL_FINISH: False
            },
            fields={'_id': 0},
            limit=1000,
            skip=0,
            sort_field=DEFINITIONS.TASK.WEIGHT
        )[1]

        tasks_by_queue_status = self._organize_tasks_by_queue(main_tasks)

        self._schedule_subtasks(tasks_by_queue_status, worker_capacity)

        self._schedule_main_tasks(tasks_by_queue_status, worker_capacity)

    @staticmethod
    def _organize_tasks_by_queue(tasks):
        """
        Organize tasks into a hierarchical structure by queue and status

        Creates a nested dictionary structure:
        {
            'queue1': {
                'WAITING': [task1, task2, ...],
                'SUCCESS': [task3, task4, ...]
            },
            'queue2': {
                'WAITING': [task5, ...],
                ...
            }
        }

        Args:
            tasks (list): List of task dictionaries to organize

        Returns:
            dict: Nested dictionary organizing tasks by queue and status
        """
        organized = {}
        for task in tasks:
            queue = task[DEFINITIONS.TASK.QUEUE_NAME]
            status = task[DEFINITIONS.TASK.STATUS]

            if queue not in organized:
                organized[queue] = {}
            if status not in organized[queue]:
                organized[queue][status] = []

            organized[queue][status].append(task)

        return organized

    def _schedule_subtasks(self, tasks_by_queue_status, worker_capacity):
        """
        Schedule subtasks for main tasks that have completed successfully

        This method handles the special case where a main task has completed
        but still has pending subtasks that need to be executed.

        Args:
            tasks_by_queue_status (dict): Tasks organized by queue and status
            worker_capacity (dict): Available capacity per worker queue
        """
        for queue_name, status_tasks in tasks_by_queue_status.items():
            if DEFINITIONS.STATUS.SUCCESS not in status_tasks:
                continue

            for main_task in status_tasks[DEFINITIONS.STATUS.SUCCESS]:
                self._process_main_task_subtasks(main_task, worker_capacity)

    def _process_main_task_subtasks(self, main_task, worker_capacity):
        """
        Process and schedule all waiting subtasks for a specific main task

        For a given successfully completed main task:
        1. Check if there are any waiting subtasks
        2. If no waiting subtasks, mark the main task as fully complete
        3. Otherwise, schedule available subtasks based on worker capacity

        Args:
            main_task (dict): The main task dictionary
            worker_capacity (dict): Available capacity per worker queue
        """
        source_id = main_task[DEFINITIONS.TASK.ID]

        waiting_subtasks = task_find_paginated(
            query={
                DEFINITIONS.TASK.SOURCE_ID: source_id,
                DEFINITIONS.TASK.STATUS: DEFINITIONS.STATUS.WAITING,
            },
            fields={'_id': 0},
            limit=1000,
            skip=0
        )[1]

        if not waiting_subtasks:
            task_collector().update(
                query={DEFINITIONS.TASK.ID: source_id},
                data={DEFINITIONS.TASK.IS_SUB_TASK_ALL_FINISH: True}
            )
            return

        for subtask in waiting_subtasks:
            subtask_queue = subtask[DEFINITIONS.TASK.QUEUE_NAME]

            if worker_capacity.get(subtask_queue, 0) < 1:
                continue

            self._dispatch_task(subtask, subtask_queue)
            worker_capacity[subtask_queue] -= 1

    def _schedule_main_tasks(self, tasks_by_queue_status, worker_capacity):
        """
        Schedule main tasks that are in WAITING status

        Processes main tasks that haven't started execution yet.
        Stops scheduling for a queue when no more capacity is available.

        Args:
            tasks_by_queue_status (dict): Tasks organized by queue and status
            worker_capacity (dict): Available capacity per worker queue
        """
        for queue_name, status_tasks in tasks_by_queue_status.items():
            if DEFINITIONS.STATUS.WAITING not in status_tasks:
                continue

            for task in status_tasks[DEFINITIONS.STATUS.WAITING]:
                if worker_capacity.get(queue_name, 0) < 1:
                    break

                self._dispatch_task(task, queue_name)
                worker_capacity[queue_name] -= 1

    def _dispatch_task(self, task, queue_name):
        """
        Dispatch a single task to the message queue and update its status

        This is the final step in task scheduling where:
        1. The task is sent to the appropriate RabbitMQ queue
        2. The task status is updated to PENDING to prevent duplicate scheduling
        3. Log entry is created for tracking purposes

        Args:
            task (dict): The task dictionary to dispatch
            queue_name (str): The target message queue name
        """
        rabbitmq_send_message(queue=queue_name, message=task[DEFINITIONS.TASK.BODY])

        self.logger.info(f'Dispatching task: {task[DEFINITIONS.TASK.ID]}')

        task_collector().update(
            query={DEFINITIONS.TASK.ID: task[DEFINITIONS.TASK.ID]},
            data={DEFINITIONS.TASK.STATUS: DEFINITIONS.STATUS.PENDING}
        )
