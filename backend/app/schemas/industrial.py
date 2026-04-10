# -*- coding: utf-8 -*-
"""
Industrial Schemas
工业资产模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 设备 ==========
class DeviceCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    device_type: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    production_line_id: Optional[str] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    production_line_id: Optional[str] = None


class DeviceResponse(BaseModel):
    id: str
    name: str
    code: str
    device_type: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: str
    health_score: float
    production_line_name: Optional[str] = None
    production_line_id: Optional[str] = None
    last_maintenance_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ========== 产线 ==========
class ProductionLineCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    location: Optional[str] = None


class ProductionLineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None


class ProductionLineResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str] = None
    location: Optional[str] = None
    status: str
    device_count: int = 0
    created_at: Optional[datetime] = None


# ========== 批次 ==========
class BatchCreate(BaseModel):
    batch_no: str = Field(..., max_length=50)
    name: Optional[str] = None
    product_type: Optional[str] = None
    quantity: int = 0
    production_line_id: Optional[str] = None


class BatchUpdate(BaseModel):
    name: Optional[str] = None
    product_type: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None


class BatchResponse(BaseModel):
    id: str
    batch_no: str
    name: Optional[str] = None
    product_type: Optional[str] = None
    quantity: int = 0
    status: str
    production_line_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
