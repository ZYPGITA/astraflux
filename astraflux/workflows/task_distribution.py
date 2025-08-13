# -*- encoding: utf-8 -*-

from astraflux.settings import *
from astraflux.interface import *


class TaskDistribution:
    """
    This class is responsible for the task distribution logic within the system.
    It interacts with RabbitMQ and databases to manage tasks, filter them based on status,
    and distribute them to appropriate workers according to the worker's idle capacity.
    """

    def __init__(self, config: dict):
        self.config = config
        initialization_logger(config=config)
        initialization_mongo(config=config)
        self.loguru = loguru(filename=KEY_PROJECT_NAME, task_id='task_distribution')

    def run(self):

        query = {
            TASK.KEY_TASK_STATUS: {
                '$in': [TASK.KEY_TASK_WAIT_STATUS, TASK.KEY_TASK_RUN_STATUS, TASK.KEY_TASK_SUCCESS_STATUS]
            }
        }
        _, source_tasks = mongodb_task().query_list_sort(
            query=query, field={'_id': 0}, limit=1000, skip_no=0, sort_field=TASK.KEY_TASK_WEIGHT)

        self.loguru.info(f'source task count === {len(source_tasks)}')

        all_tasks = {}
        source_task_status = {}
        for task in source_tasks:
            task_id = task[TASK.KEY_TASK_ID]
            task_status = task[TASK.KEY_TASK_STATUS]
            queue_name = task[TASK.KEY_TASK_QUEUE_NAME]
            is_subtask = task[TASK.KEY_TASK_IS_SUB_TASK]

            if queue_name not in all_tasks:
                all_tasks[queue_name] = {
                    TASK.KEY_TASK_RUN_STATUS: {}, TASK.KEY_TASK_WAIT_STATUS: {}, TASK.KEY_TASK_SUCCESS_STATUS: {}}

            if is_subtask is False:
                source_task_status.setdefault(task_id, {'task_status': task_status, 'source_queue_name': queue_name})
                all_tasks[queue_name][task_status][task_id] = {'body': task, 'sub_tasks': []}

        for task in source_tasks:
            task_status = task[TASK.KEY_TASK_STATUS]
            queue_name = task[TASK.KEY_TASK_QUEUE_NAME]
            is_subtask = task[TASK.KEY_TASK_IS_SUB_TASK]
            source_id = task.get(TASK.KEY_TASK_SOURCE_ID)

            if task_status != TASK.KEY_TASK_WAIT_STATUS:
                continue

            if is_subtask:
                source_status = source_task_status[source_id]['task_status']
                source_queue_name = source_task_status[source_id]['source_queue_name']
                if source_status not in [TASK.KEY_TASK_STOP_STATUS, TASK.KEY_TASK_ERROR_STATUS]:
                    all_tasks[source_queue_name][source_status][source_id]['sub_tasks'].append(
                        {'body': task, 'queue_name': queue_name})

        run_tasks = {}
        sub_task_all_finish = {}
        for queue_name in all_tasks:
            if queue_name not in run_tasks:
                run_tasks[queue_name] = []

            for task_status in [TASK.KEY_TASK_RUN_STATUS, TASK.KEY_TASK_WAIT_STATUS, TASK.KEY_TASK_SUCCESS_STATUS]:
                for source_id in all_tasks[queue_name][task_status]:
                    task = all_tasks[queue_name][task_status][source_id]
                    sub_tasks = all_tasks[queue_name][task_status][source_id]['sub_tasks']

                    if task_status == TASK.KEY_TASK_WAIT_STATUS:
                        run_tasks[queue_name].append(task['body'])
                    else:
                        if len(sub_tasks) > 0:
                            for sub in sub_tasks:
                                sub_task = sub['body']
                                sub_task_queue_name = sub['queue_name']
                                if sub_task_queue_name not in run_tasks:
                                    run_tasks[sub_task_queue_name] = []

                                run_tasks[sub_task_queue_name].append(sub_task)
                        else:
                            sub_task_all_finish.setdefault(source_id, True)

        services = mongodb_services().query_all(
            query={
                BUILD.KEY_WORKER_NAME: {'$in': [i for i in run_tasks]}},
            field={
                '_id': 0,
                BUILD.KEY_WORKER_NAME: 1,
                BUILD.KEY_WORKER_MAX_PROCESS: 1,
                BUILD.KEY_WORKER_RUN_PROCESS: 1
            },
        )

        worker_idle_number = {}
        for service in services:
            worker_name = service[BUILD.KEY_WORKER_NAME]
            worker_max_process = service[BUILD.KEY_WORKER_MAX_PROCESS]
            worker_run_process = len(service[BUILD.KEY_WORKER_RUN_PROCESS])

            if worker_name not in worker_idle_number:
                worker_idle_number[worker_name] = 0
            worker_idle_number[worker_name] += worker_max_process - worker_run_process

        for queue_name in run_tasks:
            self.loguru.info(f'services {queue_name} wait task count == {len(run_tasks[queue_name])}')

            for task in run_tasks[queue_name]:
                if worker_idle_number[queue_name] > 0:
                    rabbitmq_send_message(queue=queue_name, message=task[TASK.KEY_TASK_BODY])
                    self.loguru.info(f'run task === {task[TASK.KEY_TASK_BODY]}')
                    worker_idle_number[queue_name] -= 1

        if len(sub_task_all_finish) > 0:
            mongodb_task().update_many(
                query={TASK.KEY_TASK_ID: {'$in': [i for i in sub_task_all_finish]}},
                update_data={TASK.KEY_TASK_IS_SUB_TASK_ALL_FINISH: True}
            )
