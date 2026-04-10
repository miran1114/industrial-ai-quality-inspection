# -*- coding: utf-8 -*-
"""
Dashboard API Endpoints
仪表盘API端点
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import DataResponse
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get("/overview", response_model=DataResponse[dict], summary="获取系统总览")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await dashboard_service.get_overview(db)
    return DataResponse(data=data)


@router.get("/alerts", response_model=DataResponse[list], summary="获取最近告警")
async def get_recent_alerts(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alerts = await dashboard_service.get_recent_alerts(db, limit)
    return DataResponse(data=alerts)


@router.get("/defect-trend", response_model=DataResponse[list], summary="获取缺陷趋势")
async def get_defect_trend(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    trend = await dashboard_service.get_defect_trend(db, days)
    return DataResponse(data=trend)


@router.get("/device-health", response_model=DataResponse[list], summary="设备健康排行")
async def get_device_health_ranking(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ranking = await dashboard_service.get_device_health_ranking(db, limit)
    return DataResponse(data=ranking)
