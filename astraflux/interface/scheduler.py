# -*- encoding: utf-8 -*-


from typing import Dict, List, Callable, Optional


def add_schedule_job(job_id: str, cron_expression: str, function: Callable,
                     timezone: str = "UTC", arguments: Optional[List] = None,
                     keyword_arguments: Optional[Dict] = None, allowed_ips: Optional[List[str]] = None,
                     execution_type: str = "thread") -> bool:
    """
    Schedule a job in the distributed scheduler

    Args:
        job_id: Unique identifier for the job
        cron_expression: Cron expression for scheduling
        function: Function to be executed
        timezone: Timezone for schedule calculation
        arguments: Positional arguments for the function
        keyword_arguments: Keyword arguments for the function
        allowed_ips: List of IP addresses allowed to execute this job
        execution_type: 'thread' or 'process'

    Returns:
        Boolean indicating success
    """
    return add_schedule_job(
        job_id=job_id, cron_expression=cron_expression, function=function, timezone=timezone, arguments=arguments,
        keyword_arguments=keyword_arguments, allowed_ips=allowed_ips, execution_type=execution_type)


def remove_scheduled_job(job_id: str) -> bool:
    """
    Remove a scheduled job from the distributed scheduler

    Args:
        job_id: ID of the job to remove

    Returns:
        Boolean indicating success
    """
    return remove_scheduled_job(job_id)


def start_scheduler() -> None:
    """Start the distributed scheduler"""
    return start_scheduler()


def stop_scheduler() -> None:
    """Stop the distributed scheduler"""
    return stop_scheduler()
