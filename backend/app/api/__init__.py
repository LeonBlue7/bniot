"""
API 路由注册
"""
from fastapi import APIRouter

from app.api.endpoints import auth, devices, zones

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(devices.router, prefix="/devices", tags=["设备"])
api_router.include_router(zones.router, prefix="/zones", tags=["分区"])