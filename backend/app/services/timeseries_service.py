# -*- coding: utf-8 -*-
"""
时序分析服务
"""
import math
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker


def calculate_std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


class TimeseriesAnalysisService:
    """时序数据分析服务"""

    async def run_analysis(
        self,
        job_id: str,
        dataset_id: str,
        method: str = "zscore",
        threshold: float = 3.0,
        start_time=None,
        end_time=None,
    ):
        """执行异常检测分析"""
        from app.models.system import AnalysisJob
        from app.models.timeseries import TimeseriesDataset, TimeseriesPoint, TimeseriesAnomaly

        async with async_session_maker() as db:
            try:
                # Update job status
                job_result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
                job = job_result.scalar_one_or_none()
                if not job:
                    return
                job.status = "running"
                job.started_at = datetime.utcnow()
                await db.commit()

                # Get data points
                query = select(TimeseriesPoint).where(TimeseriesPoint.dataset_id == dataset_id)
                if start_time:
                    query = query.where(TimeseriesPoint.timestamp >= start_time)
                if end_time:
                    query = query.where(TimeseriesPoint.timestamp <= end_time)
                query = query.order_by(TimeseriesPoint.timestamp)

                result = await db.execute(query)
                points = result.scalars().all()

                if not points:
                    job.status = "completed"
                    job.result = {"message": "无数据点", "anomalies_found": 0}
                    job.completed_at = datetime.utcnow()
                    await db.commit()
                    return

                values = [p.value for p in points if p.value is not None]
                if not values:
                    job.status = "completed"
                    job.result = {"message": "无有效数值", "anomalies_found": 0}
                    job.completed_at = datetime.utcnow()
                    await db.commit()
                    return

                mean = sum(values) / len(values)
                std = calculate_std(values)

                anomalies_found = 0
                for p in points:
                    if p.value is None:
                        continue
                    if std > 0:
                        z_score = abs(p.value - mean) / std
                    else:
                        z_score = 0

                    if z_score > threshold:
                        if z_score > threshold * 2:
                            severity = "high"
                        elif z_score > threshold * 1.5:
                            severity = "medium"
                        else:
                            severity = "low"

                        anomaly = TimeseriesAnomaly(
                            id=uuid.uuid4(),
                            dataset_id=uuid.UUID(dataset_id) if isinstance(dataset_id, str) else dataset_id,
                            anomaly_type="point_anomaly",
                            severity=severity,
                            timestamp=p.timestamp,
                            start_time=p.timestamp,
                            end_time=p.timestamp,
                            value=p.value,
                            score=round(z_score, 4),
                            threshold=threshold,
                            detection_method=method,
                            description=f"Z-Score={round(z_score, 2)}, 阈值={threshold}",
                        )
                        db.add(anomaly)
                        anomalies_found += 1

                job.status = "completed"
                job.progress = 100.0
                job.result = {
                    "total_points": len(points),
                    "anomalies_found": anomalies_found,
                    "method": method,
                    "threshold": threshold,
                    "statistics": {
                        "mean": round(mean, 4),
                        "std": round(std, 4),
                        "min": round(min(values), 4),
                        "max": round(max(values), 4),
                    },
                }
                job.completed_at = datetime.utcnow()
                await db.commit()

            except Exception as e:
                job_result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
                job = job_result.scalar_one_or_none()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    await db.commit()

    def analyze_statistics(self, values: List[float]) -> Dict:
        """基础统计分析"""
        if not values:
            return {}
        n = len(values)
        mean = sum(values) / n
        sorted_v = sorted(values)
        median = sorted_v[n // 2] if n % 2 == 1 else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2
        std = calculate_std(values)
        cv = std / mean if mean != 0 else 0

        return {
            "count": n,
            "mean": round(mean, 4),
            "std": round(std, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "median": round(median, 4),
            "cv": round(cv, 4),
        }

    def detect_trend(self, values: List[float]) -> Dict:
        """趋势检测（线性回归）"""
        n = len(values)
        if n < 3:
            return {"direction": "unknown", "slope": 0}

        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return {"direction": "stable", "slope": 0}

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        ss_res = sum((values[i] - (slope * i + intercept)) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        predicted_next = slope * n + intercept

        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "rising"
        else:
            direction = "falling"

        return {
            "direction": direction,
            "slope": round(slope, 6),
            "intercept": round(intercept, 4),
            "r_squared": round(r_squared, 4),
            "predicted_next": round(predicted_next, 4),
        }


timeseries_service = TimeseriesAnalysisService()
