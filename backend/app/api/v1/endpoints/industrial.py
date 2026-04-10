# -*- coding: utf-8 -*-
"""
Industrial API Endpoints
工业资产API端点 - 设备、产线、批次管理
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import DeviceNotFoundError, ResourceNotFoundError
from app.models.user import User
from app.models.industrial import Device, ProductionLine, Batch
from app.schemas.industrial import (
    DeviceCreate, DeviceUpdate, DeviceResponse,
    ProductionLineCreate, ProductionLineUpdate, ProductionLineResponse,
    BatchCreate, BatchUpdate, BatchResponse,
)
from app.schemas.common import ResponseBase, DataResponse, PaginatedResponse, PaginationMeta
from app.services.audit_service import AuditService

router = APIRouter()


# ========== 设备管理 ==========

@router.get("/devices", response_model=PaginatedResponse[DeviceResponse], summary="获取设备列表")
async def list_devices(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    production_line_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Device).options(selectinload(Device.production_line))
    count_query = select(func.count(Device.id))

    if search:
        sf = or_(Device.name.ilike(f"%{search}%"), Device.code.ilike(f"%{search}%"))
        query = query.where(sf)
        count_query = count_query.where(sf)

    if status:
        query = query.where(Device.status == status)
        count_query = count_query.where(Device.status == status)

    if production_line_id:
        query = query.where(Device.production_line_id == production_line_id)
        count_query = count_query.where(Device.production_line_id == production_line_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Device.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    devices = result.scalars().all()

    device_list = [
        DeviceResponse(
            id=str(d.id), name=d.name, code=d.code,
            device_type=d.device_type, model=d.model,
            manufacturer=d.manufacturer, serial_number=d.serial_number,
            description=d.description, location=d.location,
            status=d.status, health_score=d.health_score or 100.0,
            production_line_name=d.production_line.name if d.production_line else None,
            production_line_id=str(d.production_line_id) if d.production_line_id else None,
            last_maintenance_at=d.last_maintenance_at,
            created_at=d.created_at, updated_at=d.updated_at,
        )
        for d in devices
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=device_list,
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
        ),
    )


@router.post("/devices", response_model=DataResponse[DeviceResponse], summary="创建设备")
async def create_device(
    request: Request,
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device = Device(
        id=uuid.uuid4(),
        name=device_data.name,
        code=device_data.code,
        device_type=device_data.device_type,
        model=device_data.model,
        manufacturer=device_data.manufacturer,
        serial_number=device_data.serial_number,
        description=device_data.description,
        location=device_data.location,
        production_line_id=device_data.production_line_id,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="create", resource_type="device", resource_id=str(device.id),
        description=f"创建设备 {device.name}", request=request,
    )

    return DataResponse(
        data=DeviceResponse(
            id=str(device.id), name=device.name, code=device.code,
            device_type=device.device_type, model=device.model,
            manufacturer=device.manufacturer, status=device.status,
            health_score=device.health_score or 100.0,
            created_at=device.created_at,
        )
    )


@router.get("/devices/{device_id}", response_model=DataResponse[DeviceResponse], summary="获取设备详情")
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).options(selectinload(Device.production_line)).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise DeviceNotFoundError(device_id)

    return DataResponse(
        data=DeviceResponse(
            id=str(device.id), name=device.name, code=device.code,
            device_type=device.device_type, model=device.model,
            manufacturer=device.manufacturer, serial_number=device.serial_number,
            description=device.description, location=device.location,
            status=device.status, health_score=device.health_score or 100.0,
            production_line_name=device.production_line.name if device.production_line else None,
            production_line_id=str(device.production_line_id) if device.production_line_id else None,
            last_maintenance_at=device.last_maintenance_at,
            created_at=device.created_at, updated_at=device.updated_at,
        )
    )


@router.put("/devices/{device_id}", response_model=DataResponse[DeviceResponse], summary="更新设备")
async def update_device(
    request: Request,
    device_id: str,
    update_data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise DeviceNotFoundError(device_id)

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(device, key, value)

    await db.commit()
    await db.refresh(device)

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="update", resource_type="device", resource_id=device_id,
        description=f"更新设备 {device.name}", request=request,
    )

    return DataResponse(
        data=DeviceResponse(
            id=str(device.id), name=device.name, code=device.code,
            device_type=device.device_type, model=device.model,
            manufacturer=device.manufacturer, status=device.status,
            health_score=device.health_score or 100.0,
            created_at=device.created_at, updated_at=device.updated_at,
        )
    )


@router.delete("/devices/{device_id}", response_model=ResponseBase, summary="删除设备")
async def delete_device(
    request: Request,
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise DeviceNotFoundError(device_id)

    device_name = device.name
    await db.delete(device)
    await db.commit()

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="delete", resource_type="device", resource_id=device_id,
        description=f"删除设备 {device_name}", request=request,
    )
    return ResponseBase(message="设备删除成功")


# ========== 产线管理 ==========

@router.get("/production-lines", response_model=PaginatedResponse[ProductionLineResponse], summary="获取产线列表")
async def list_production_lines(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ProductionLine).options(selectinload(ProductionLine.devices))
    count_query = select(func.count(ProductionLine.id))

    if search:
        sf = or_(ProductionLine.name.ilike(f"%{search}%"), ProductionLine.code.ilike(f"%{search}%"))
        query = query.where(sf)
        count_query = count_query.where(sf)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(ProductionLine.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    lines = result.scalars().unique().all()

    line_list = [
        ProductionLineResponse(
            id=str(pl.id), name=pl.name, code=pl.code,
            description=pl.description, location=pl.location,
            status=pl.status, device_count=len(pl.devices),
            created_at=pl.created_at,
        )
        for pl in lines
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=line_list,
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
        ),
    )


@router.post("/production-lines", response_model=DataResponse[ProductionLineResponse], summary="创建产线")
async def create_production_line(
    request: Request,
    line_data: ProductionLineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    line = ProductionLine(
        id=uuid.uuid4(),
        name=line_data.name,
        code=line_data.code,
        description=line_data.description,
        location=line_data.location,
    )
    db.add(line)
    await db.commit()
    await db.refresh(line)

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="create", resource_type="production_line", resource_id=str(line.id),
        description=f"创建产线 {line.name}", request=request,
    )

    return DataResponse(
        data=ProductionLineResponse(
            id=str(line.id), name=line.name, code=line.code,
            description=line.description, location=line.location,
            status=line.status, device_count=0, created_at=line.created_at,
        )
    )


@router.delete("/production-lines/{line_id}", response_model=ResponseBase, summary="删除产线")
async def delete_production_line(
    request: Request,
    line_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProductionLine).where(ProductionLine.id == line_id))
    line = result.scalar_one_or_none()
    if not line:
        raise ResourceNotFoundError("产线", line_id)

    line_name = line.name
    await db.delete(line)
    await db.commit()

    await AuditService.log(
        db=db, user_id=current_user.id, username=current_user.username,
        action="delete", resource_type="production_line", resource_id=line_id,
        description=f"删除产线 {line_name}", request=request,
    )
    return ResponseBase(message="产线删除成功")


# ========== 批次管理 ==========

@router.get("/batches", response_model=PaginatedResponse[BatchResponse], summary="获取批次列表")
async def list_batches(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    production_line_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Batch).options(selectinload(Batch.production_line))
    count_query = select(func.count(Batch.id))

    if search:
        sf = or_(Batch.batch_no.ilike(f"%{search}%"), Batch.name.ilike(f"%{search}%"))
        query = query.where(sf)
        count_query = count_query.where(sf)

    if production_line_id:
        query = query.where(Batch.production_line_id == production_line_id)
        count_query = count_query.where(Batch.production_line_id == production_line_id)

    if status:
        query = query.where(Batch.status == status)
        count_query = count_query.where(Batch.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Batch.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    batches = result.scalars().all()

    batch_list = [
        BatchResponse(
            id=str(b.id), batch_no=b.batch_no, name=b.name,
            product_type=b.product_type, quantity=b.quantity,
            status=b.status,
            production_line_name=b.production_line.name if b.production_line else None,
            start_time=b.start_time, end_time=b.end_time,
            created_at=b.created_at,
        )
        for b in batches
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=batch_list,
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
        ),
    )


@router.post("/batches", response_model=DataResponse[BatchResponse], summary="创建批次")
async def create_batch(
    request: Request,
    batch_data: BatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    batch = Batch(
        id=uuid.uuid4(),
        batch_no=batch_data.batch_no,
        name=batch_data.name,
        product_type=batch_data.product_type,
        quantity=batch_data.quantity,
        production_line_id=batch_data.production_line_id,
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    return DataResponse(
        data=BatchResponse(
            id=str(batch.id), batch_no=batch.batch_no, name=batch.name,
            product_type=batch.product_type, quantity=batch.quantity,
            status=batch.status, created_at=batch.created_at,
        )
    )
