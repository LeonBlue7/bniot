"""
文档 API 端点

提供错误码文档等辅助功能。
"""
from fastapi import APIRouter

from app.core.errors import ErrorResponse, get_all_error_codes

router = APIRouter()


@router.get("/error-codes")
async def get_error_codes_documentation():
    """
    获取错误码文档

    返回所有错误码的定义，包括：
    - 错误码标识
    - 错误消息
    - HTTP 状态码
    - 错误描述

    用于客户端开发参考和错误处理。
    """
    return {
        "total": len(get_all_error_codes()),
        "error_codes": get_all_error_codes()
    }