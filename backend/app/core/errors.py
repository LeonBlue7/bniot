"""
错误码定义模块

提供标准化的错误码定义、错误响应格式和 HTTP 状态码映射。
用于 API 文档增强和统一错误处理。
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """
    标准错误码定义

    错误码格式: CATEGORY_NUMBER (如 AUTH_001, DEVICE_001)

    分类:
    - AUTH: 认证相关错误 (100-199)
    - PERMISSION: 权限相关错误 (200-299)
    - VALIDATION: 验证相关错误 (300-399)
    - RESOURCE: 资源相关错误 (400-499)
    - DEVICE: 设备相关错误 (500-599)
    - SYSTEM: 系统相关错误 (600-699)
    """

    # ============ 认证错误 (100-199) ============
    AUTH_001 = "AUTH_001"
    AUTH_002 = "AUTH_002"
    AUTH_003 = "AUTH_003"
    AUTH_004 = "AUTH_004"
    AUTH_005 = "AUTH_005"

    # ============ 权限错误 (200-299) ============
    PERMISSION_001 = "PERMISSION_001"
    PERMISSION_002 = "PERMISSION_002"
    PERMISSION_003 = "PERMISSION_003"

    # ============ 验证错误 (300-399) ============
    VALIDATION_001 = "VALIDATION_001"
    VALIDATION_002 = "VALIDATION_002"
    VALIDATION_003 = "VALIDATION_003"
    VALIDATION_004 = "VALIDATION_004"

    # ============ 资源错误 (400-499) ============
    RESOURCE_001 = "RESOURCE_001"
    RESOURCE_002 = "RESOURCE_002"
    RESOURCE_003 = "RESOURCE_003"
    RESOURCE_004 = "RESOURCE_004"

    # ============ 设备错误 (500-599) ============
    DEVICE_001 = "DEVICE_001"
    DEVICE_002 = "DEVICE_002"
    DEVICE_003 = "DEVICE_003"
    DEVICE_004 = "DEVICE_004"

    # ============ 系统错误 (600-699) ============
    SYSTEM_001 = "SYSTEM_001"
    SYSTEM_002 = "SYSTEM_002"
    SYSTEM_003 = "SYSTEM_003"


# 错误码详细信息定义
ERROR_DETAILS: dict[ErrorCode, dict[str, Any]] = {
    # ============ 认证错误 ============
    ErrorCode.AUTH_001: {
        "message": "用户名或密码错误",
        "http_status": 401,
        "description": "登录时提供的用户名或密码不正确"
    },
    ErrorCode.AUTH_002: {
        "message": "用户已禁用",
        "http_status": 400,
        "description": "用户账户已被管理员禁用"
    },
    ErrorCode.AUTH_003: {
        "message": "登录尝试过于频繁",
        "http_status": 429,
        "description": "短时间内登录失败次数过多，已被临时限制"
    },
    ErrorCode.AUTH_004: {
        "message": "令牌无效或已过期",
        "http_status": 401,
        "description": "JWT 令牌无效、已过期或格式错误"
    },
    ErrorCode.AUTH_005: {
        "message": "缺少认证令牌",
        "http_status": 401,
        "description": "请求缺少 Authorization 头"
    },

    # ============ 权限错误 ============
    ErrorCode.PERMISSION_001: {
        "message": "无权限访问",
        "http_status": 403,
        "description": "用户没有执行此操作的权限"
    },
    ErrorCode.PERMISSION_002: {
        "message": "无权限访问该资源",
        "http_status": 403,
        "description": "用户没有访问特定资源的权限"
    },
    ErrorCode.PERMISSION_003: {
        "message": "需要管理员权限",
        "http_status": 403,
        "description": "此操作需要管理员角色"
    },

    # ============ 验证错误 ============
    ErrorCode.VALIDATION_001: {
        "message": "请求参数验证失败",
        "http_status": 422,
        "description": "请求参数不符合预期格式或约束"
    },
    ErrorCode.VALIDATION_002: {
        "message": "缺少必填参数",
        "http_status": 422,
        "description": "请求缺少必需的参数"
    },
    ErrorCode.VALIDATION_003: {
        "message": "参数格式无效",
        "http_status": 422,
        "description": "参数格式不符合要求"
    },
    ErrorCode.VALIDATION_004: {
        "message": "参数值超出范围",
        "http_status": 422,
        "description": "参数值不在允许的范围内"
    },

    # ============ 资源错误 ============
    ErrorCode.RESOURCE_001: {
        "message": "资源不存在",
        "http_status": 404,
        "description": "请求的资源不存在或已被删除"
    },
    ErrorCode.RESOURCE_002: {
        "message": "资源ID已存在",
        "http_status": 400,
        "description": "创建资源时，提供的ID已存在"
    },
    ErrorCode.RESOURCE_003: {
        "message": "资源已被其他租户使用",
        "http_status": 400,
        "description": "资源已被其他租户占用，无法访问"
    },
    ErrorCode.RESOURCE_004: {
        "message": "资源已存在",
        "http_status": 409,
        "description": "资源已存在，无法重复创建"
    },

    # ============ 设备错误 ============
    ErrorCode.DEVICE_001: {
        "message": "设备不存在",
        "http_status": 404,
        "description": "指定的设备不存在或无权访问"
    },
    ErrorCode.DEVICE_002: {
        "message": "设备ID已存在",
        "http_status": 400,
        "description": "创建设备时，提供的设备ID已存在"
    },
    ErrorCode.DEVICE_003: {
        "message": "设备离线",
        "http_status": 400,
        "description": "设备当前处于离线状态，无法执行操作"
    },
    ErrorCode.DEVICE_004: {
        "message": "MQTT通信失败",
        "http_status": 500,
        "description": "与设备的MQTT通信失败"
    },

    # ============ 系统错误 ============
    ErrorCode.SYSTEM_001: {
        "message": "服务器内部错误",
        "http_status": 500,
        "description": "服务器发生未预期的错误"
    },
    ErrorCode.SYSTEM_002: {
        "message": "数据库错误",
        "http_status": 500,
        "description": "数据库操作失败"
    },
    ErrorCode.SYSTEM_003: {
        "message": "服务暂时不可用",
        "http_status": 503,
        "description": "服务正在维护或暂时不可用"
    },
}


class ErrorResponse(BaseModel):
    """
    标准错误响应格式

    所有 API 错误响应应使用此格式，确保客户端能够统一处理错误。
    """
    code: str = Field(..., description="错误码，用于精确识别错误类型")
    message: str = Field(..., description="错误消息，人类可读的描述")
    details: dict[str, Any] | None = Field(
        default=None,
        description="错误详情，包含额外的上下文信息"
    )
    http_status: int = Field(..., description="HTTP 状态码")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "DEVICE_001",
                "message": "设备不存在",
                "details": {"device_id": 12345},
                "http_status": 404
            }
        }


def get_error_info(error_code: ErrorCode) -> dict[str, Any]:
    """
    获取错误码的详细信息

    Args:
        error_code: 错误码枚举值

    Returns:
        包含 message, http_status, description 的字典
    """
    return ERROR_DETAILS.get(error_code, {
        "message": "未知错误",
        "http_status": 500,
        "description": "未知错误类型"
    })


def create_error_response(
    error_code: ErrorCode,
    details: dict[str, Any] | None = None
) -> ErrorResponse:
    """
    创建标准错误响应

    Args:
        error_code: 错误码枚举值
        details: 额外的错误详情

    Returns:
        ErrorResponse 对象
    """
    info = get_error_info(error_code)
    return ErrorResponse(
        code=error_code.value,
        message=info["message"],
        details=details,
        http_status=info["http_status"]
    )


def get_all_error_codes() -> list[dict[str, Any]]:
    """
    获取所有错误码定义（用于文档）

    Returns:
        包含所有错误码信息的列表
    """
    result = []
    for error_code in ErrorCode:
        info = get_error_info(error_code)
        result.append({
            "code": error_code.value,
            "name": error_code.name,
            "message": info["message"],
            "http_status": info["http_status"],
            "description": info["description"]
        })
    return result