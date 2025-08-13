AstraFlux 使用文档
=================

.. code-block:: bash

    使用NexusFlow框架以极简的配置快速搭建分布式任务系统. 功能:
    1. 异步/定时任务
    2. 分布式任务
    3. 服务注册, 服务监控, 动态配置注入, 负载均衡


框架初始化
========

.. code-block:: bash

    1. 创建config.yaml文件

    Mongodb:
      host: 127.0.0.1
      port: 27017
      db: nexusflow
      username: scheduleAdmin
      password: scheduleAdminPassword

    Redis:
      host: 127.0.0.1
      port: 6379
      password: scheduleAdminPassword

    RabbitMQ:
      host: 127.0.0.1
      port: 5672
      username: scheduleAdmin
      password: scheduleAdminPassword

    logger:
      level: INFO

    2. 在main.py中初始化框架

    import os
    os_dir = os.path.dirname(__file__)
    nf = AstraFlux('config.yaml', os_dir)


服务注册
======

1. 创建test_server.py文件

.. code-block:: bash

    # -*- coding: utf-8 -*-

    from nexusflow import *


    class RpcFunction(ServiceConstructor):
        service_name = 'test_server'

        """
        系统会自动代理所有函数,并提供RCP调用方式
        """

        def get_service_name(self):
            return {"service_version": self.service_version}

        def test_func(self, **args):
            return args

    class WorkerFunction(WorkerConstructor):
        worker_name = 'test_server'

        def run(self, data):
            self.loguru.info(data)
            """
            当任务队列 worker_name 内有新增任务时,调度器根据当前服务、节点
            创建work后执行‌本函数, 在此处实现业务逻辑, data为任务所有数据
            """

2. 在main.py中注册服务

.. code-block:: bash

    import test_server # 引入py脚本
    nf.registry(services=[test_server])

    nf.start()


定时/异步任务
===========

.. code-block:: bash

    from nexusflow import *

    def test_task(name):
        print(name)

    # 创建异步任务, 只在创建的机器运行
    async_task_add(
        task_id='test_001', # 任务ID
        task_type='process', #  任务类型, process:进程/thread:线程
        target=test_task, # 任务函数
        args=('111',) # 函数入参
    )

    # 创建分布式定时任务, 只需添加一次所有允许的机器都会运行
    scheduler_add_job(
        task_id='test_002',  # 任务ID
        cron_str='0 0/1 * * * *',  # 6位数corn表达式
        func_object=test,  # 任务函数
        args=('222',),  # 函数入参
        exec_type='thread',  # 任务类型, process:进程/thread:线程
        ipaddrs=['127.0.0.1'] # 允许运行该任务的机器IP, 所有机器都允许时该参数不传
    )

    # 运行任务
    async_task_run_all()
    async_task_wait_all()

    # 启动定时调度器
    scheduler_start()

函数使用说明
===========


.. code-block:: bash

    # 所有函数都可以在interface下查看详细注释, 本文档只说明常用函数
    from nexusflow.interface import *

    # 获取雪花ID
    _id = snowflake_id()

    # 创建任务
    message = {'task_id': 'test_003', 'status': 'wait', 'name': 'xxxx'}
    task_submit_databases(queue='test_server', message=message)

    # 创建子任务, 适用任务分片. 调度器会自动监控任务, 所有子任务完成时自动更新主任务状态
    subtask_create(
        source_task_id='test_003',
        subtask_queue='test_server_sub', # 任务队列名称, 参考test_server.py开发任务逻辑处理函数
        subtasks=[
            {
                'task_id': snowflake_id(),
                'name': 'subtask1',
            }
        ]
    )

    # 停止任务
    task_stop(task_id='test_003')

    # 获取mongodb操作实例, 返回一个对象封装常用pymongo操作.具体信息查看函数注释
    mongodb_task() # 任务信息
    mongodb_node() # 节点信息
    mongodb_services() # 服务信息

    # 获取redis操作实例
    redis_task()
    redis_services()

    # rpc调用服务函数, 调度器根据服务运行状态自动选择最优节点
    d = proxy_call(
        service_name='test_server',
        method_name='test_func',

        # 函数入参
        a=1, b=2
    )
