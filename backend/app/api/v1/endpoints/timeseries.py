# -*- coding: utf-8 -*-
"""
Timeseries API Endpoints
时序分析API端点
"""
import os
import uuid
import math
import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError
from app.models.user import User
from app.models.timeseries import TimeseriesDataset, TimeseriesPoint, TimeseriesAnomaly, AnalysisReport
from app.models.system import AnalysisJob
from app.schemas.timeseries import (
    TimeseriesDatasetResponse, TimeseriesDatasetListResponse,
    TimeseriesPointResponse, TimeseriesDataResponse,
    SimulateDataRequest, TimeseriesAnalysisRequest,
    TriggerAnalysisResponse, TimeseriesAnomalyResponse, AnalysisReportResponse,
)
from app.schemas.common import ResponseBase, DataResponse, PaginatedResponse, PaginationMeta
from app.services.audit_service import AuditService
from app.services.timeseries_service import timeseries_service, calculate_std

router = APIRouter()


def generate_normal_random(mean=0, std=1):
    u1 = random.random()
    u2 = random.random()
    z = math.sqrt(-2 * math.log(max(u1, 1e-10))) * math.cos(2 * math.pi * u2)
    return mean + z * std


def generate_random_value():
    return random.random()


def random_select(choices):
    return random.choice(choices)


def generate_uniform_random(a, b):
    return random.uniform(a, b)


@router.post("/datasets/simulate", response_model=DataResponse[TimeseriesDatasetResponse], summary="生成模拟数据")
async def simulate_timeseries_data(
    request: Request,
    sim_request: SimulateDataRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dataset = TimeseriesDataset(
        id=uuid.uuid4(),
        name=sim_request.name,
        description=sim_request.description,
        source_type="simulated",
        device_id=sim_request.device_id if sim_request.device_id else None,
        created_by=current_user.id,
        status="active",
        extra_data={
            "sensor_name": sim_request.sensor_name,
            "parameter_name": sim_request.parameter_name,
            "unit": sim_request.unit,
        },
    )
    db.add(dataset)
    await db.flush()

    points = []
    values = []
    timestamps = []
    current_time = sim_request.start_time
    step = 0

    while current_time <= sim_request.end_time:
        value = sim_request.base_value + \
                sim_request.trend_slope * step + \
                generate_normal_random(0, sim_request.noise_std)

        if generate_random_value() < sim_request.anomaly_ratio:
            anomaly_factor = random_select([-1, 1]) * generate_uniform_random(3, 5)
            value += anomaly_factor * sim_request.noise_std

        point = TimeseriesPoint(
            id=uuid.uuid4(),
            dataset_id=dataset.id,
            timestamp=current_time,
            value=value,
            quality=100,
        )
        points.append(point)
        values.append(value)
        timestamps.append(current_time)

        current_time += timedelta(seconds=sim_request.frequency_seconds)
        step += 1

    if points:
        db.add_all(points)        
        dataset.total_points = len(points)
        dataset.start_time = min(timestamps)
        dataset.end_time = max(timestamps)
        extra = dataset.extra_data or {}
        extra.update({
            "min_value": float(min(values)),
            "max_value": float(max(values)),
            "mean_value": float(sum(values) / len(values)),
            "std_value": float(calculate_std(values)),
        })
        dataset.extra_data = extra

        await db.commit()

    await db.refresh(dataset)
    extra = dataset.extra_data or {}

    return DataResponse(
        data=TimeseriesDatasetResponse(
            id=str(dataset.id), name=dataset.name, description=dataset.description,
            source_type=dataset.source_type,
            device_id=str(dataset.device_id) if dataset.device_id else None,
            sensor_name=extra.get("sensor_name"),
            parameter_name=extra.get("parameter_name"),
            unit=extra.get("unit"),
            start_time=dataset.start_time, end_time=dataset.end_time,
            point_count=dataset.total_points or 0,
            min_value=extra.get("min_value"), max_value=extra.get("max_value"),
            mean_value=extra.get("mean_value"), std_value=extra.get("std_value"),
            status=dataset.status, created_at=dataset.created_at,
        ),
        message=f"模拟数据生成成功，共 {len(points)} 个数据点",
    )


@router.get("/datasets", response_model=PaginatedResponse[TimeseriesDatasetListResponse], summary="获取数据集列表")
async def list_timeseries_datasets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    device_id: Optional[str] = None,
    source_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(TimeseriesDataset).options(selectinload(TimeseriesDataset.device))
    count_query = select(func.count(TimeseriesDataset.id))

    if search:
        sf = or_(
            TimeseriesDataset.name.ilike(f"%{search}%"),
            TimeseriesDataset.description.ilike(f"%{search}%"),
        )
        query = query.where(sf)
        count_query = count_query.where(sf)

    if device_id:
        query = query.where(TimeseriesDataset.device_id == device_id)
        count_query = count_query.where(TimeseriesDataset.device_id == device_id)

    if source_type:
        query = query.where(TimeseriesDataset.source_type == source_type)
        count_query = count_query.where(TimeseriesDataset.source_type == source_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(TimeseriesDataset.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    datasets = result.scalars().all()

    dataset_list = [
        TimeseriesDatasetListResponse(
            id=str(d.id), name=d.name,
            device_name=d.device.name if d.device else None,
            sensor_name=d.extra_data.get("sensor_name") if d.extra_data else None,
            point_count=d.total_points or 0,
            start_time=d.start_time, end_time=d.end_time,
            status=d.status, created_at=d.created_at,
        )
        for d in datasets
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=dataset_list,
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
        ),
    )


@router.get("/datasets/{dataset_id}", response_model=DataResponse[TimeseriesDatasetResponse], summary="获取数据集详情")
async def get_timeseries_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TimeseriesDataset)
        .options(selectinload(TimeseriesDataset.device))
        .where(TimeseriesDataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise ResourceNotFoundError("时序数据集", dataset_id)

    extra = dataset.extra_data or {}
    return DataResponse(
        data=TimeseriesDatasetResponse(
            id=str(dataset.id), name=dataset.name, description=dataset.description,
            source_type=dataset.source_type, file_path=dataset.file_path,
            file_name=extra.get("file_name"),
            device_id=str(dataset.device_id) if dataset.device_id else None,
            device_name=dataset.device.name if dataset.device else None,
            sensor_name=extra.get("sensor_name"),
            parameter_name=extra.get("parameter_name"),
            unit=extra.get("unit"),
            start_time=dataset.start_time, end_time=dataset.end_time,
            point_count=dataset.total_points or 0,
            min_value=extra.get("min_value"), max_value=extra.get("max_value"),
            mean_value=extra.get("mean_value"), std_value=extra.get("std_value"),
            status=dataset.status,
            uploaded_by=str(dataset.created_by) if dataset.created_by else None,
            created_at=dataset.created_at,
        )
    )


@router.get("/datasets/{dataset_id}/data", response_model=DataResponse[TimeseriesDataResponse], summary="获取时序数据")
async def get_timeseries_data(
    dataset_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=1000, le=10000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TimeseriesDataset).where(TimeseriesDataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise ResourceNotFoundError("时序数据集", dataset_id)

    query = select(TimeseriesPoint).where(TimeseriesPoint.dataset_id == dataset_id)
    if start_time:
        query = query.where(TimeseriesPoint.timestamp >= start_time)
    if end_time:
        query = query.where(TimeseriesPoint.timestamp <= end_time)
    query = query.order_by(TimeseriesPoint.timestamp).limit(limit)

    result = await db.execute(query)
    points = result.scalars().all()

    point_responses = [
        TimeseriesPointResponse(timestamp=p.timestamp, value=p.value, quality=p.quality or 100)
        for p in points
    ]

    statistics = None
    if points:
        vals = [p.value for p in points if p.value is not None]
        if vals:
            statistics = {
                "count": len(vals),
                "min": min(vals),
                "max": max(vals),
                "mean": sum(vals) / len(vals),
                "std": calculate_std(vals),
            }

    return DataResponse(
        data=TimeseriesDataResponse(
            dataset_id=str(dataset.id), dataset_name=dataset.name,
            unit=(dataset.extra_data or {}).get("unit"),
            points=point_responses, statistics=statistics,
        )
    )


@router.post("/analyze", response_model=DataResponse[TriggerAnalysisResponse], summary="触发时序分析")
async def trigger_timeseries_analysis(
    request: Request,
    analysis_request: TimeseriesAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TimeseriesDataset).where(TimeseriesDataset.id == analysis_request.dataset_id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise ResourceNotFoundError("时序数据集", analysis_request.dataset_id)

    job = AnalysisJob(
        id=uuid.uuid4(),
        name=f"时序分析-{dataset.name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        job_type="anomaly_detection",
        description=f"分析数据集: {dataset.name}",
        status="pending",
        input_params={
            "dataset_id": analysis_request.dataset_id,
            "start_time": analysis_request.start_time.isoformat() if analysis_request.start_time else None,
            "end_time": analysis_request.end_time.isoformat() if analysis_request.end_time else None,
            "analysis_types": analysis_request.analysis_types,
            "anomaly_method": analysis_request.anomaly_method,
            "anomaly_threshold": analysis_request.anomaly_threshold,
        },
        dataset_id=uuid.UUID(analysis_request.dataset_id) if isinstance(analysis_request.dataset_id, str) else analysis_request.dataset_id,
        created_by=current_user.id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(
        timeseries_service.run_analysis,
        str(job.id),
        analysis_request.dataset_id,
        analysis_request.anomaly_method,
        analysis_request.anomaly_threshold,
        analysis_request.start_time,
        analysis_request.end_time,
    )

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="trigger_analysis", resource_type="timeseries_analysis",
        resource_id=str(job.id),
        description=f"触发时序分析任务: {dataset.name}", request=request,
    )

    return DataResponse(
        data=TriggerAnalysisResponse(
            job_id=str(job.id), dataset_id=analysis_request.dataset_id,
            message="分析任务已创建",
        )
    )


@router.get("/anomalies", response_model=PaginatedResponse[TimeseriesAnomalyResponse], summary="获取异常点列表")
async def list_timeseries_anomalies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    dataset_id: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_confirmed: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(TimeseriesAnomaly)
    count_query = select(func.count(TimeseriesAnomaly.id))

    if dataset_id:
        query = query.where(TimeseriesAnomaly.dataset_id == dataset_id)
        count_query = count_query.where(TimeseriesAnomaly.dataset_id == dataset_id)
    if anomaly_type:
        query = query.where(TimeseriesAnomaly.anomaly_type == anomaly_type)
        count_query = count_query.where(TimeseriesAnomaly.anomaly_type == anomaly_type)
    if severity:
        query = query.where(TimeseriesAnomaly.severity == severity)
        count_query = count_query.where(TimeseriesAnomaly.severity == severity)
    if is_confirmed is not None:
        query = query.where(TimeseriesAnomaly.is_confirmed == is_confirmed)
        count_query = count_query.where(TimeseriesAnomaly.is_confirmed == is_confirmed)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(TimeseriesAnomaly.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    anomalies = result.scalars().all()

    anomaly_list = [
        TimeseriesAnomalyResponse(
            id=str(a.id), dataset_id=str(a.dataset_id),
            timestamp=a.timestamp, value=a.value,
            anomaly_type=a.anomaly_type, severity=a.severity,
            score=a.score, detection_method=a.detection_method,
            threshold=a.threshold, description=a.description,
            is_confirmed=a.is_confirmed,
            is_false_positive=a.is_false_positive,
            created_at=a.created_at,
        )
        for a in anomalies
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=anomaly_list,
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
        ),
    )


@router.get("/reports", response_model=PaginatedResponse[AnalysisReportResponse], summary="获取分析报告列表")
async def list_analysis_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    report_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AnalysisReport)
    count_query = select(func.count(AnalysisReport.id))

    if report_type:
        query = query.where(AnalysisReport.report_type == report_type)
        count_query = count_query.where(AnalysisReport.report_type == report_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(AnalysisReport.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reports = result.scalars().all()

    report_list = [
        AnalysisReportResponse(
            id=str(r.id), title=r.title, report_type=r.report_type,
            description=r.description, content_json=r.content_json,
            content_markdown=r.content_markdown,
            dataset_id=str(r.dataset_id) if r.dataset_id else None,
            device_id=str(r.device_id) if r.device_id else None,
            job_id=str(r.job_id) if r.job_id else None,
            export_path=r.export_path,
            created_by=str(r.created_by) if r.created_by else None,
            created_at=r.created_at,
        )
        for r in reports
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=report_list,
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
        ),
    )


@router.delete("/datasets/{dataset_id}", response_model=ResponseBase, summary="删除数据集")
async def delete_timeseries_dataset(
    request: Request,
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TimeseriesDataset).where(TimeseriesDataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise ResourceNotFoundError("时序数据集", dataset_id)

    dataset_name = dataset.name
    if dataset.file_path and os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)

    await db.delete(dataset)
    await db.commit()

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="delete", resource_type="timeseries_dataset", resource_id=dataset_id,
        description=f"删除时序数据集 {dataset_name}", request=request,
    )
    return ResponseBase(message="数据集删除成功")
