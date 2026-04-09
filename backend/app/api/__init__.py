"""
API 路由注册
"""
from fastapi import APIRouter

from app.api.endpoints import alarms, auth, devices, reports, users, websocket, zones

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["告警"])
api_router.include_router(devices.router, prefix="/devices", tags=["设备"])
api_router.include_router(zones.router, prefix="/zones", tags=["分区"])
api_router.include_router(reports.router, prefix="/reports", tags=["报表"])
api_router.include_router(websocket.router, tags=["WebSocket"])
