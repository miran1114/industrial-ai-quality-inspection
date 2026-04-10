# -*- coding: utf-8 -*-
"""
Defect API Endpoints
缺陷检测API端点
"""
import os
import uuid
import random
from datetime import datetime
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
from app.models.defect import DefectSample, DefectResult, DefectType
from app.schemas.defect import (
    DefectSampleResponse, DefectSampleListResponse,
    DefectDetectRequest, DefectResultResponse,
    DefectTypeCreate, DefectTypeResponse,
)
from app.schemas.common import ResponseBase, DataResponse, PaginatedResponse, PaginationMeta
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/samples", response_model=PaginatedResponse[DefectSampleListResponse], summary="获取样本列表")
async def list_defect_samples(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    device_id: Optional[str] = None,
    batch_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(DefectSample).options(
        selectinload(DefectSample.device),
        selectinload(DefectSample.batch),
        selectinload(DefectSample.defect_results),
    )
    count_query = select(func.count(DefectSample.id))

    if search:
        sf = or_(
            DefectSample.sample_no.ilike(f"%{search}%"),
            DefectSample.name.ilike(f"%{search}%"),
        )
        query = query.where(sf)
        count_query = count_query.where(sf)

    if status:
        query = query.where(DefectSample.status == status)
        count_query = count_query.where(DefectSample.status == status)

    if device_id:
        query = query.where(DefectSample.device_id == device_id)
        count_query = count_query.where(DefectSample.device_id == device_id)

    if batch_id:
        query = query.where(DefectSample.batch_id == batch_id)
        count_query = count_query.where(DefectSample.batch_id == batch_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(DefectSample.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    samples = result.scalars().unique().all()

    sample_list = [
        DefectSampleListResponse(
            id=str(s.id),
            sample_no=s.sample_no,
            name=s.name,
            file_name=s.file_name,
            device_name=s.device.name if s.device else None,
            batch_no=s.batch.batch_no if s.batch else None,
            status=s.status,
            has_defect=any(r.has_defect for r in s.defect_results) if s.defect_results else None,
            created_at=s.created_at,
        )
        for s in samples
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=sample_list,
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
        ),
    )


@router.post("/samples/upload", response_model=DataResponse[DefectSampleResponse], summary="上传缺陷样本")
async def upload_defect_sample(
    request: Request,
    file: UploadFile = File(...),
    sample_no: str = Form(...),
    name: str = Form(None),
    device_id: str = Form(None),
    batch_id: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, "defects")
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    safe_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, safe_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    sample = DefectSample(
        id=uuid.uuid4(),
        sample_no=sample_no,
        name=name or file.filename,
        file_path=file_path,
        file_name=file.filename,
        file_size=len(content),
        file_type=file.content_type,
        source="upload",
        device_id=device_id if device_id else None,
        batch_id=batch_id if batch_id else None,
        uploaded_by=current_user.id,
        status="pending",
    )
    db.add(sample)
    await db.commit()
    await db.refresh(sample)

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="upload", resource_type="defect_sample", resource_id=str(sample.id),
        description=f"上传缺陷样本 {sample.sample_no}", request=request,
    )

    return DataResponse(
        data=DefectSampleResponse(
            id=str(sample.id), sample_no=sample.sample_no, name=sample.name,
            file_name=sample.file_name, file_size=sample.file_size,
            file_type=sample.file_type, status=sample.status,
            created_at=sample.created_at,
        ),
        message="样本上传成功",
    )


@router.get("/samples/{sample_id}", response_model=DataResponse[DefectSampleResponse], summary="获取样本详情")
async def get_defect_sample(
    sample_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DefectSample)
        .options(
            selectinload(DefectSample.device),
            selectinload(DefectSample.batch),
            selectinload(DefectSample.defect_results),
        )
        .where(DefectSample.id == sample_id)
    )
    sample = result.scalar_one_or_none()
    if not sample:
        raise ResourceNotFoundError("缺陷样本", sample_id)

    return DataResponse(
        data=DefectSampleResponse(
            id=str(sample.id), sample_no=sample.sample_no, name=sample.name,
            sample_type=sample.sample_type,
            file_name=sample.file_name, file_size=sample.file_size,
            file_type=sample.file_type,
            image_width=sample.image_width, image_height=sample.image_height,
            device_name=sample.device.name if sample.device else None,
            batch_no=sample.batch.batch_no if sample.batch else None,
            status=sample.status,
            has_defect=any(r.has_defect for r in sample.defect_results) if sample.defect_results else None,
            created_at=sample.created_at,
        )
    )


@router.post("/detect", response_model=DataResponse[list], summary="触发缺陷检测")
async def trigger_defect_detection(
    request: Request,
    detect_request: DefectDetectRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """触发缺陷检测 - 模拟检测结果"""
    results = []
    for sample_id in detect_request.sample_ids:
        result = await db.execute(select(DefectSample).where(DefectSample.id == sample_id))
        sample = result.scalar_one_or_none()
        if not sample:
            continue

        # Simulated detection result
        has_defect = random.random() > 0.7
        confidence = round(random.uniform(0.75, 0.99), 4)

        defect_result = DefectResult(
            id=uuid.uuid4(),
            sample_id=sample.id,
            has_defect=has_defect,
            confidence=confidence,
            bbox=[random.randint(10, 200), random.randint(10, 200),
                  random.randint(200, 400), random.randint(200, 400)] if has_defect else None,
            model_name=detect_request.detector,
            model_version="1.0.0",
        )
        db.add(defect_result)

        sample.status = "completed"

        results.append(DefectResultResponse(
            id=str(defect_result.id),
            sample_id=str(sample.id),
            sample_no=sample.sample_no,
            has_defect=has_defect,
            confidence=confidence,
            bbox=defect_result.bbox,
            model_name=detect_request.detector,
            created_at=defect_result.created_at,
        ).model_dump())

    await db.commit()

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="detect", resource_type="defect_detection",
        description=f"触发缺陷检测，样本数: {len(detect_request.sample_ids)}",
        request=request,
    )

    return DataResponse(data=results, message=f"检测完成，处理了 {len(results)} 个样本")


@router.delete("/samples/{sample_id}", response_model=ResponseBase, summary="删除样本")
async def delete_defect_sample(
    request: Request,
    sample_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DefectSample).where(DefectSample.id == sample_id))
    sample = result.scalar_one_or_none()
    if not sample:
        raise ResourceNotFoundError("缺陷样本", sample_id)

    # Delete file
    if sample.file_path and os.path.exists(sample.file_path):
        os.remove(sample.file_path)

    sample_no = sample.sample_no
    await db.delete(sample)
    await db.commit()

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="delete", resource_type="defect_sample", resource_id=sample_id,
        description=f"删除缺陷样本 {sample_no}", request=request,
    )
    return ResponseBase(message="样本删除成功")
