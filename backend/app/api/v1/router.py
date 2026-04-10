# -*- coding: utf-8 -*-
"""
API Router
API路由注册
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, industrial, defects, timeseries, dashboard, notifications

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(industrial.router, prefix="/industrial", tags=["工业资产"])
api_router.include_router(defects.router, prefix="/defect", tags=["缺陷检测"])
api_router.include_router(timeseries.router, prefix="/timeseries", tags=["时序分析"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知"])
