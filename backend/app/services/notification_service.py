# -*- coding: utf-8 -*-
"""
通知服务
"""
import uuid
from datetime import datetime
from typing import Dict, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class NotificationService:
    """系统通知管理"""

    @classmethod
    async def send(cls, db: AsyncSession, user_id, title: str, content: str,
                   notification_type: str = "info",
                   related_type: str = None, related_id=None,
                   extra_data: Dict = None):
        from app.models.system import Notification

        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            content=content,
            notification_type=notification_type,
            related_type=related_type,
            related_id=related_id,
            extra_data=extra_data,
        )
        db.add(notification)
        await db.flush()
        return notification

    @classmethod
    async def send_batch(cls, db: AsyncSession, user_ids: List, title: str, content: str,
                         notification_type: str = "info"):
        notifications = []
        for uid in user_ids:
            n = await cls.send(db, uid, title, content, notification_type)
            notifications.append(n)
        return notifications

    @classmethod
    async def mark_read(cls, db: AsyncSession, notification_id: str, user_id):
        from app.models.system import Notification

        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await db.flush()
        return notification

    @classmethod
    async def mark_all_read(cls, db: AsyncSession, user_id):
        from app.models.system import Notification

        result = await db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        notifications = result.scalars().all()
        now = datetime.utcnow()
        for n in notifications:
            n.is_read = True
            n.read_at = now
        await db.flush()
        return len(notifications)

    @classmethod
    async def get_unread_count(cls, db: AsyncSession, user_id) -> int:
        from app.models.system import Notification

        result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        return result.scalar() or 0

    @classmethod
    async def get_notifications(cls, db: AsyncSession, user_id, page: int = 1,
                                page_size: int = 20, unread_only: bool = False) -> Dict:
        from app.models.system import Notification

        query = select(Notification).where(Notification.user_id == user_id)
        count_query = select(func.count(Notification.id)).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)
            count_query = count_query.where(Notification.is_read == False)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        notifications = result.scalars().all()

        return {
            "items": [
                {
                    "id": str(n.id),
                    "title": n.title,
                    "content": n.content,
                    "type": n.notification_type,
                    "is_read": n.is_read,
                    "read_at": n.read_at.isoformat() if n.read_at else None,
                    "related_type": n.related_type,
                    "related_id": str(n.related_id) if n.related_id else None,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in notifications
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "unread_count": await cls.get_unread_count(db, user_id),
        }


notification_service = NotificationService()
