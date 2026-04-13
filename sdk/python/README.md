# BNIoT Python SDK

空调节能管理系统物联网平台的 Python 客户端 SDK。

## 安装

```bash
pip install bniot-sdk
```

或从源码安装：

```bash
git clone https://github.com/your-repo/bniot.git
cd sdk/python
pip install -e .
```

## 快速开始

### 认证登录

```python
from bniot_client import BNIoTClient

# 创建客户端
client = BNIoTClient(base_url="https://www.jxbonner.cloud/api")

# 登录
client.login("username", "password")

# 登录成功后，token 会自动保存，后续请求自动携带认证
```

### 设备管理

```python
# 获取设备列表
devices = client.get_devices()
print(f"共有 {len(devices)} 台设备")

# 获取单个设备详情
device = client.get_device(1)
print(f"设备名称: {device['name']}")

# 创建新设备
new_device = client.create_device({
    "device_id": "IMEI12345678",
    "name": "空调-会议室"
})

# 更新设备
client.update_device(1, {"name": "空调-新名称"})

# 删除设备
client.delete_device(1)
```

### 设备控制

```python
# 远程开机
client.control_device(1, airstate=1)

# 远程关机
client.control_device(1, airstate=0)
```

### 批量操作

```python
# 批量开机
result = client.batch_control([1, 2, 3], airstate=1)
print(f"成功: {result['success_count']}, 失败: {result['failed_count']}")

# 批量删除
result = client.batch_delete([1, 2, 3])
```

### 告警管理

```python
# 获取告警列表
alarms = client.get_alarms(is_resolved=False)

# 处理告警
client.resolve_alarm(1)
```

### WebSocket 实时推送

```python
# 连接 WebSocket
client.connect_websocket()

# 设置消息回调
client.on_device_update = lambda data: print(f"设备更新: {data}")
client.on_alarm = lambda data: print(f"新告警: {data}")

# 断开连接
client.disconnect_websocket()
```

## 错误处理

```python
from bniot_client import BNIoTClient, BNIoTError

try:
    device = client.get_device(999)
except BNIoTError as e:
    print(f"错误码: {e.code}")
    print(f"错误消息: {e.message}")
    print(f"HTTP 状态码: {e.http_status}")
```

## 配置选项

```python
client = BNIoTClient(
    base_url="https://www.jxbonner.cloud/api",
    timeout=30,  # 请求超时时间（秒）
    retry_count=3,  # 失败重试次数
    verify_ssl=True  # SSL 证书验证
)
```

## API 文档

完整 API 文档请访问：https://www.jxbonner.cloud/api/docs

## 许可证

MIT License