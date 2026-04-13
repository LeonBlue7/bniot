"""
批量操作示例 - 设备批量控制和删除

演示如何使用 BNIoT SDK 进行批量操作。
"""
from bniot_client import BNIoTClient, BNIoTError


def main():
    # 创建并登录
    client = BNIoTClient(base_url="https://www.jxbonner.cloud/api")
    client.login("your_username", "your_password")

    try:
        # 获取设备列表
        devices = client.get_devices(limit=100)
        if len(devices) < 3:
            print("设备数量不足，跳过批量操作演示")
            return

        device_ids = [d['id'] for d in devices[:3]]
        print(f"选定设备: {device_ids}")

        # 批量开机
        print("\n批量开机...")
        result = client.batch_control(device_ids, airstate=1)
        print(f"成功: {result['success_count']}")
        print(f"失败: {result['failed_count']}")
        if result['failed_details']:
            print(f"失败详情: {result['failed_details']}")

        # 批量关机
        print("\n批量关机...")
        result = client.batch_control(device_ids, airstate=0)
        print(f"成功: {result['success_count']}")

        # 批量迁移分区（示例）
        print("\n批量迁移分区（仅演示）...")
        # result = client.batch_move_zone(device_ids, zone_id=2)
        # print(f"迁移结果: {result}")

        # 批量删除（危险操作，仅演示）
        print("\n批量删除（不实际执行）...")
        # result = client.batch_delete([test_device_id])
        # print(f"删除结果: {result}")

    except BNIoTError as e:
        print(f"批量操作失败: [{e.code}] {e.message}")


if __name__ == "__main__":
    main()