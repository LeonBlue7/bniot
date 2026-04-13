"""
BNIoT Python SDK 客户端

提供完整的 API 调用封装，支持认证、设备管理、告警处理等功能。
"""
import json
import time
from typing import Any
from urllib.parse import urljoin

import requests
import websocket


class BNIoTError(Exception):
    """BNIoT API 错误"""

    def __init__(self, code: str, message: str, http_status: int, details: dict | None = None):
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details
        super().__init__(f"[{code}] {message}")


class BNIoTClient:
    """
    BNIoT 空调节能管理系统 SDK 客户端

    使用方法:
        client = BNIoTClient(base_url="https://www.jxbonner.cloud/api")
        client.login("username", "password")
        devices = client.get_devices()
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        retry_count: int = 3,
        verify_ssl: bool = True
    ):
        """
        初始化客户端

        Args:
            base_url: API 基础 URL
            timeout: 请求超时时间（秒）
            retry_count: 失败重试次数
            verify_ssl: 是否验证 SSL 证书
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.verify_ssl = verify_ssl
        self.token: str | None = None
        self.ws: websocket.WebSocketApp | None = None

        # WebSocket 回调
        self.on_device_update: callable | None = None
        self.on_alarm: callable | None = None
        self.on_connect: callable | None = None
        self.on_disconnect: callable | None = None

    def _request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        params: dict | None = None,
        require_auth: bool = True
    ) -> dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法
            path: API 路径
            data: 请求体数据
            params: URL 参数
            require_auth: 是否需要认证

        Returns:
            响应数据

        Raises:
            BNIoTError: API 错误
        """
        url = urljoin(self.base_url, path)
        headers = {}

        if require_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        for attempt in range(self.retry_count):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )

                if response.status_code >= 400:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    raise BNIoTError(
                        code=error_data.get("code", "SYSTEM_001"),
                        message=error_data.get("message", error_data.get("detail", response.text)),
                        http_status=response.status_code,
                        details=error_data.get("details")
                    )

                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == self.retry_count - 1:
                    raise BNIoTError(
                        code="SYSTEM_001",
                        message=f"网络请求失败: {str(e)}",
                        http_status=500
                    )
                time.sleep(1)

        return {}

    # ============ 认证 ============

    def login(self, username: str, password: str) -> dict[str, Any]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            包含 token 的响应

        Raises:
            BNIoTError: 登录失败
        """
        response = self._request(
            "POST",
            "/auth/login",
            data={"username": username, "password": password},
            require_auth=False
        )
        self.token = response.get("access_token")
        return response

    def get_current_user(self) -> dict[str, Any]:
        """
        获取当前用户信息

        Returns:
            用户信息字典
        """
        return self._request("GET", "/auth/me")

    def get_csrf_token(self) -> dict[str, Any]:
        """
        获取 CSRF Token

        Returns:
            包含 csrf_token 的响应
        """
        return self._request("GET", "/auth/csrf-token", require_auth=False)

    # ============ 设备管理 ============

    def get_devices(
        self,
        zone_id: int | None = None,
        is_online: bool | None = None,
        keyword: str | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        获取设备列表

        Args:
            zone_id: 分区 ID 过滤
            is_online: 是否在线过滤
            keyword: 关键词搜索
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            设备列表
        """
        params = {"skip": skip, "limit": limit}
        if zone_id:
            params["zone_id"] = zone_id
        if is_online is not None:
            params["is_online"] = is_online
        if keyword:
            params["keyword"] = keyword

        return self._request("GET", "/devices", params=params)

    def get_device(self, device_id: int) -> dict[str, Any]:
        """
        获取设备详情

        Args:
            device_id: 设备 ID

        Returns:
            设备详情
        """
        return self._request("GET", f"/devices/{device_id}")

    def get_device_data(
        self,
        device_id: int,
        hours: int = 24
    ) -> list[dict[str, Any]]:
        """
        获取设备历史数据

        Args:
            device_id: 设备 ID
            hours: 查询最近 N 小时数据

        Returns:
            历史数据列表
        """
        return self._request("GET", f"/devices/{device_id}/data", params={"hours": hours})

    def create_device(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        创建设备

        Args:
            data: 设备数据（device_id, name, zone_id 等）

        Returns:
            创建的设备信息
        """
        return self._request("POST", "/devices", data=data)

    def update_device(self, device_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """
        更新设备

        Args:
            device_id: 设备 ID
            data: 更新数据

        Returns:
            更新后的设备信息
        """
        return self._request("PUT", f"/devices/{device_id}", data=data)

    def delete_device(self, device_id: int) -> dict[str, Any]:
        """
        删除设备

        Args:
            device_id: 设备 ID

        Returns:
            操作结果
        """
        return self._request("DELETE", f"/devices/{device_id}")

    def control_device(self, device_id: int, airstate: int) -> dict[str, Any]:
        """
        远程控制设备

        Args:
            device_id: 设备 ID
            airstate: 控制状态（0关机，1开机）

        Returns:
            操作结果
        """
        return self._request(
            "POST",
            f"/devices/{device_id}/control",
            params={"airstate": airstate}
        )

    # ============ 批量操作 ============

    def batch_control(
        self,
        device_ids: list[int],
        airstate: int
    ) -> dict[str, Any]:
        """
        批量控制设备

        Args:
            device_ids: 设备 ID 列表
            airstate: 控制状态（0关机，1开机）

        Returns:
            批量操作结果
        """
        return self._request(
            "POST",
            "/devices/batch/control",
            data={"device_ids": device_ids, "airstate": airstate}
        )

    def batch_delete(self, device_ids: list[int]) -> dict[str, Any]:
        """
        批量删除设备

        Args:
            device_ids: 设备 ID 列表

        Returns:
            批量操作结果
        """
        return self._request(
            "POST",
            "/devices/batch/delete",
            data={"device_ids": device_ids}
        )

    def batch_move_zone(
        self,
        device_ids: list[int],
        zone_id: int | None
    ) -> dict[str, Any]:
        """
        批量迁移设备分区

        Args:
            device_ids: 设备 ID 列表
            zone_id: 目标分区 ID（None 表示移出分区）

        Returns:
            批量操作结果
        """
        return self._request(
            "POST",
            "/devices/batch/move-zone",
            data={"device_ids": device_ids, "zone_id": zone_id}
        )

    # ============ 告警管理 ============

    def get_alarms(
        self,
        is_resolved: bool | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        获取告警列表

        Args:
            is_resolved: 是否已处理过滤
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            告警列表
        """
        params = {"skip": skip, "limit": limit}
        if is_resolved is not None:
            params["is_resolved"] = is_resolved

        return self._request("GET", "/alarms", params=params)

    def resolve_alarm(self, alarm_id: int) -> dict[str, Any]:
        """
        处理告警

        Args:
            alarm_id: 告警 ID

        Returns:
            操作结果
        """
        return self._request(
            "PUT",
            f"/alarms/{alarm_id}",
            data={"is_resolved": True}
        )

    # ============ 分区管理 ============

    def get_zones(self) -> list[dict[str, Any]]:
        """
        获取分区列表

        Returns:
            分区列表
        """
        return self._request("GET", "/zones")

    def create_zone(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        创建分区

        Args:
            data: 分区数据（name, description 等）

        Returns:
            创建的分区信息
        """
        return self._request("POST", "/zones", data=data)

    # ============ 统计数据 ============

    def get_dashboard_stats(self) -> dict[str, Any]:
        """
        获取仪表盘统计数据

        Returns:
            统计数据（设备总数、在线数、告警数等）
        """
        return self._request("GET", "/devices/stats")

    # ============ WebSocket ============

    def connect_websocket(self) -> None:
        """
        连接 WebSocket 实时推送

        连接成功后，可通过设置回调函数接收实时消息：
        - on_device_update: 设备数据更新
        - on_alarm: 新告警
        """
        ws_url = urljoin(self.base_url, "/ws").replace("http", "ws")

        def on_message(ws, message):
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "device_update" and self.on_device_update:
                self.on_device_update(data)
            elif msg_type == "alarm" and self.on_alarm:
                self.on_alarm(data)

        def on_open(ws):
            if self.on_connect:
                self.on_connect()

        def on_close(ws, close_status_code, close_msg):
            if self.on_disconnect:
                self.on_disconnect()

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_open=on_open,
            on_close=on_close,
            header={"Authorization": f"Bearer {self.token}"} if self.token else {}
        )
        self.ws.run_forever()

    def disconnect_websocket(self) -> None:
        """
        断开 WebSocket 连接
        """
        if self.ws:
            self.ws.close()
            self.ws = None


# 示例用法
if __name__ == "__main__":
    # 创建客户端
    client = BNIoTClient(base_url="http://localhost:5000/api")

    # 登录
    try:
        client.login("admin", "admin123")
        print("登录成功")

        # 获取设备列表
        devices = client.get_devices()
        print(f"设备列表: {devices}")

        # 获取统计
        stats = client.get_dashboard_stats()
        print(f"统计数据: {stats}")

    except BNIoTError as e:
        print(f"错误: {e}")