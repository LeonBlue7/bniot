"""
认证示例 - 用户登录和获取信息

演示如何使用 BNIoT SDK 进行用户认证。
"""
from bniot_client import BNIoTClient, BNIoTError


def main():
    # 创建客户端
    client = BNIoTClient(
        base_url="https://www.jxbonner.cloud/api",
        timeout=30
    )

    try:
        # 登录
        print("正在登录...")
        login_result = client.login("your_username", "your_password")
        print(f"登录成功! Token: {login_result['access_token']}")

        # 获取当前用户信息
        print("\n获取用户信息...")
        user = client.get_current_user()
        print(f"用户名: {user['username']}")
        print(f"角色: {user['role']}")
        print(f"租户ID: {user['tenant_id']}")

        # 获取 CSRF Token
        print("\n获取 CSRF Token...")
        csrf = client.get_csrf_token()
        print(f"CSRF Token: {csrf['csrf_token']}")

    except BNIoTError as e:
        print(f"登录失败!")
        print(f"错误码: {e.code}")
        print(f"错误消息: {e.message}")
        print(f"HTTP状态: {e.http_status}")
        if e.details:
            print(f"详情: {e.details}")


if __name__ == "__main__":
    main()