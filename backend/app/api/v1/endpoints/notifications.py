# -*- coding: utf-8 -*-
"""
Notifications API Endpoints
通知API端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ResponseBase, DataResponse
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=DataResponse[dict], summary="获取通知列表")
async def get_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_read: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    unread_only = is_read is False if is_read is not None else False
    result = await NotificationService.get_notifications(
        db, current_user.id, page, page_size, unread_only
    )
    return DataResponse(data=result)


@router.get("/unread-count", response_model=DataResponse[int], summary="获取未读通知数")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await NotificationService.get_unread_count(db, current_user.id)
    return DataResponse(data=count)


@router.post("/{notification_id}/read", response_model=ResponseBase, summary="标记通知已读")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await NotificationService.mark_read(db, notification_id, current_user.id)
    await db.commit()
    return ResponseBase(message="已标记为已读")


@router.post("/read-all", response_model=ResponseBase, summary="标记所有已读")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await NotificationService.mark_all_read(db, current_user.id)
    await db.commit()
    return ResponseBase(message=f"已标记 {count} 条通知为已读")
