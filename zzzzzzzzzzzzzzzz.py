import os

from astraflux import *

current_dir = os.path.dirname(__file__)

af = AstraFlux(yaml_path=f'{current_dir}/config.yaml', current_dir=current_dir)

logger().info('Test ----')

# data1 = {
#     "unique_id": "test_server_172.19.32.134",
#     "name": "astraflux_test_server",
#     "service_functions": {
#         "get_service_name": []
#     },
#     "service_ipaddr": "172.19.32.134",
#     "service_name": "test_server",
#     "service_pid": 2941089,
#     "service_version": "20251211092959",
#     "worker_functions": {
#         "run": [
#             {
#                 "param_name": "data",
#                 "default_value": None
#             }
#         ]
#     },
#     "worker_ipaddr": "172.19.32.134",
#     "worker_max_process": 10,
#     "worker_name": "test_server",
#     "worker_pid": 2941121,
#     "worker_run_process": [2941122, 2941123, 2941124],
#     "worker_version": "20251211092959"
# }
# redis_store_worker_data(data1)
#
# # 使用示例
# if __name__ == "__main__":
#     # 2. 高频查询max_process
#     max_process = redis_get_max_process(data1['unique_id'])
#     print(f"Worker max process: {max_process}")
#
#     # 3. 更新max_process
#     redis_update_max_process(data1['unique_id'], 15)
#
#     # 4. 原子递增max_process
#     new_max = redis_increment_max_process(data1['unique_id'], 3)
#     print(f"Incremented max process: {new_max}")
#
#     # 5. 查询run_process数量
#     run_count = redis_get_run_process_count(data1['unique_id'])
#     print(f"Run process count: {run_count}")
#
#     # 6. 添加进程到run_process
#     redis_add_to_run_process(data1['unique_id'], 2941125)
#     redis_add_to_run_process(data1['unique_id'], 2941126)
#
#     # 8. 移除进程
#     redis_remove_from_run_process(data1['unique_id'], 2941122)
#
#     # 9. 获取所有run_process
#     run_process_list = redis_get_all_run_process(data1['unique_id'])
#     print(f"All run processes: {run_process_list}")
#
#     # 10. 计算可用槽位
#     available_slots = redis_get_available_slots(data1['unique_id'])
#     print(f"Available slots: {available_slots}")
#
#     # 11. 获取worker状态摘要（高频查询优化）
#     status = redis_get_worker_status(data1['unique_id'])
#     print(f"Worker status: {status}")
#
#     # 12. 获取完整数据
#     full_data = redis_get_full_worker_data(data1['unique_id'])
#     print(f"Full worker data keys: {list(full_data.keys()) if full_data else []}")
#
#     # 13. 根据服务名称查找worker
#     workers = redis_scan_workers_by_service("test_server")
#     print(f"Workers for test_server: {workers}")
