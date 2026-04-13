"""
设备管理示例 - 设备 CRUD 操作

演示如何使用 BNIoT SDK 进行设备管理。
"""
from bniot_client import BNIoTClient, BNIoTError


def main():
    # 创建并登录
    client = BNIoTClient(base_url="https://www.jxbonner.cloud/api")
    client.login("your_username", "your_password")

    try:
        # 获取设备列表
        print("获取设备列表...")
        devices = client.get_devices(limit=10)
        print(f"找到 {len(devices)} 台设备")

        for device in devices[:3]:
            print(f"  - ID: {device['id']}, 名称: {device['name']}, 在线: {device['is_online']}")

        # 搜索设备
        print("\n搜索设备...")
        search_result = client.get_devices(keyword="会议室")
        print(f"搜索结果: {len(search_result)} 台")

        # 获取单个设备详情
        if devices:
            device_id = devices[0]['id']
            print(f"\n获取设备 {device_id} 详情...")
            device = client.get_device(device_id)
            print(f"设备名称: {device['name']}")
            print(f"设备ID: {device['device_id']}")
            print(f"协议版本: {device['protocol_version']}")

            # 获取设备历史数据
            print(f"\n获取设备 {device_id} 最近24小时数据...")
            data = client.get_device_data(device_id, hours=24)
            if data:
                latest = data[0]
                print(f"温度: {latest.get('temp')}C")
                print(f"湿度: {latest.get('humi')}%")
                print(f"空调状态: {latest.get('airstate')}")

        # 创建新设备（示例）
        print("\n创建新设备（仅演示，实际不执行）...")
        # new_device = client.create_device({
        #     "device_id": "IMEI12345678",
        #     "name": "测试空调",
        #     "zone_id": 1
        # })
        # print(f"创建成功: {new_device}")

        # 获取仪表盘统计
        print("\n获取仪表盘统计...")
        stats = client.get_dashboard_stats()
        print(f"总设备数: {stats['total_devices']}")
        print(f"在线设备: {stats['online_devices']}")
        print(f"离线设备: {stats['offline_devices']}")
        print(f"未处理告警: {stats['unresolved_alarms']}")

    except BNIoTError as e:
        print(f"操作失败: [{e.code}] {e.message}")


if __name__ == "__main__":
    main()