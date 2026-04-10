# -*- coding: utf-8 -*-
"""
审计日志服务
"""
import uuid
from datetime import datetime
from typing import Dict, Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class AuditService:
    """审计日志记录和查询"""

    SENSITIVE_FIELDS = {"password", "token", "secret", "hashed_password", "access_token", "refresh_token"}

    @classmethod
    async def log(
        cls,
        db: AsyncSession,
        user_id,
        username: str,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        description: str = "",
        old_value: Dict = None,
        new_value: Dict = None,
        request=None,
    ):
        from app.models.system import AuditLog

        ip_address = None
        user_agent = None
        if request:
            ip_address = cls._extract_ip(request)
            user_agent = request.headers.get("user-agent", "")

        log_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"description": description},
            old_value=cls._filter_sensitive(old_value) if old_value else None,
            new_value=cls._filter_sensitive(new_value) if new_value else None,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            status="success",
        )

        db.add(log_entry)
        try:
            await db.flush()
        except Exception:
            pass

    @classmethod
    def _extract_ip(cls, request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        if hasattr(request, "client") and request.client:
            return request.client.host
        return "unknown"

    @classmethod
    def _filter_sensitive(cls, data: Dict) -> Dict:
        if not isinstance(data, dict):
            return data
        filtered = {}
        for key, value in data.items():
            if key.lower() in cls.SENSITIVE_FIELDS:
                filtered[key] = "***"
            elif isinstance(value, dict):
                filtered[key] = cls._filter_sensitive(value)
            else:
                filtered[key] = value
        return filtered

    @classmethod
    async def query_logs(
        cls,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        user_id=None,
        action: str = None,
        resource_type: str = None,
        start_date=None,
        end_date=None,
    ) -> Dict:
        from app.models.system import AuditLog

        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))

        conditions = []
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        for c in conditions:
            query = query.where(c)
            count_query = count_query.where(c)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AuditLog.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        logs = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": [
                {
                    "id": str(log.id),
                    "username": log.username,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "status": log.status,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
