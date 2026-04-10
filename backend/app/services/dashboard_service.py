# -*- coding: utf-8 -*-
"""
仪表盘数据聚合服务
"""
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class DashboardService:
    """仪表盘统计数据聚合"""

    async def get_overview(self, db: AsyncSession) -> Dict:
        from app.models.industrial import Device, ProductionLine
        from app.models.defect import DefectSample, DefectResult
        from app.models.timeseries import TimeseriesDataset, TimeseriesAnomaly

        device_count = await self._count(db, Device)
        online_count = await self._count_where(db, Device, Device.status == "online")
        offline_count = await self._count_where(db, Device, Device.status == "offline")
        warning_count = await self._count_where(db, Device, Device.status == "warning")

        line_count = await self._count(db, ProductionLine)
        sample_count = await self._count(db, DefectSample)
        defect_count = await self._count_where(db, DefectResult, DefectResult.has_defect == True)
        dataset_count = await self._count(db, TimeseriesDataset)
        anomaly_count = await self._count(db, TimeseriesAnomaly)

        return {
            "devices": {
                "total": device_count,
                "online": online_count,
                "offline": offline_count,
                "warning": warning_count,
                "online_rate": round(online_count / device_count * 100, 1) if device_count > 0 else 0,
            },
            "production_lines": line_count,
            "defect_detection": {
                "total_samples": sample_count,
                "defect_found": defect_count,
                "defect_rate": round(defect_count / sample_count * 100, 2) if sample_count > 0 else 0,
            },
            "timeseries": {
                "datasets": dataset_count,
                "anomalies_detected": anomaly_count,
            },
        }

    async def get_recent_alerts(self, db: AsyncSession, limit: int = 10) -> List[Dict]:
        from app.models.system import Notification

        result = await db.execute(
            select(Notification)
            .where(Notification.notification_type == "alert")
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        notifications = result.scalars().all()

        return [
            {
                "id": str(n.id),
                "title": n.title,
                "content": n.content,
                "type": n.notification_type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ]

    async def get_defect_trend(self, db: AsyncSession, days: int = 30) -> List[Dict]:
        from app.models.defect import DefectResult

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        result = await db.execute(
            select(DefectResult)
            .where(DefectResult.created_at >= start_date)
            .order_by(DefectResult.created_at)
        )
        all_results = result.scalars().all()

        daily_stats = {}
        for r in all_results:
            day_key = r.created_at.strftime("%Y-%m-%d")
            if day_key not in daily_stats:
                daily_stats[day_key] = {"total": 0, "defect": 0}
            daily_stats[day_key]["total"] += 1
            if r.has_defect:
                daily_stats[day_key]["defect"] += 1

        trend = []
        current = start_date
        while current <= end_date:
            day_str = current.strftime("%Y-%m-%d")
            stats = daily_stats.get(day_str, {"total": 0, "defect": 0})
            rate = round(stats["defect"] / stats["total"] * 100, 2) if stats["total"] > 0 else 0
            trend.append({
                "date": day_str,
                "total": stats["total"],
                "defect": stats["defect"],
                "rate": rate,
            })
            current += timedelta(days=1)

        return trend

    async def get_device_health_ranking(self, db: AsyncSession, limit: int = 20) -> List[Dict]:
        from app.models.industrial import Device

        result = await db.execute(
            select(Device).order_by(Device.health_score.asc()).limit(limit)
        )
        devices = result.scalars().all()

        ranking = []
        for idx, d in enumerate(devices, 1):
            score = d.health_score if d.health_score is not None else 100.0
            if score >= 85:
                level = "good"
            elif score >= 60:
                level = "fair"
            elif score >= 40:
                level = "poor"
            else:
                level = "critical"
            ranking.append({
                "rank": idx,
                "device_id": str(d.id),
                "device_name": d.name,
                "device_code": d.code,
                "health_score": score,
                "level": level,
                "status": d.status,
                "last_maintenance": d.last_maintenance_at.isoformat() if d.last_maintenance_at else None,
            })

        return ranking

    async def _count(self, db: AsyncSession, model):
        result = await db.execute(select(func.count(model.id)))
        return result.scalar() or 0

    async def _count_where(self, db: AsyncSession, model, condition):
        result = await db.execute(select(func.count(model.id)).where(condition))
        return result.scalar() or 0


dashboard_service = DashboardService()
