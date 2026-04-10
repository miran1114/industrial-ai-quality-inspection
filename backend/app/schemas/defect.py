# -*- coding: utf-8 -*-
"""
Defect Schemas
缺陷检测模型
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class DefectSampleCreate(BaseModel):
    sample_no: str = Field(..., max_length=100)
    name: Optional[str] = None
    sample_type: Optional[str] = None
    device_id: Optional[str] = None
    batch_id: Optional[str] = None


class DefectSampleResponse(BaseModel):
    id: str
    sample_no: str
    name: Optional[str] = None
    sample_type: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    device_name: Optional[str] = None
    batch_no: Optional[str] = None
    status: str
    has_defect: Optional[bool] = None
    created_at: Optional[datetime] = None


class DefectSampleListResponse(BaseModel):
    id: str
    sample_no: str
    name: Optional[str] = None
    file_name: Optional[str] = None
    device_name: Optional[str] = None
    batch_no: Optional[str] = None
    status: str
    has_defect: Optional[bool] = None
    created_at: Optional[datetime] = None


class DefectDetectRequest(BaseModel):
    sample_ids: List[str]
    detector: str = "default"


class DefectResultResponse(BaseModel):
    id: str
    sample_id: str
    sample_no: Optional[str] = None
    has_defect: bool
    confidence: float
    defect_type_name: Optional[str] = None
    bbox: Optional[Any] = None
    model_name: Optional[str] = None
    created_at: Optional[datetime] = None


class DefectTypeCreate(BaseModel):
    name: str
    code: str
    category: Optional[str] = None
    severity: str = "medium"
    description: Optional[str] = None


class DefectTypeResponse(BaseModel):
    id: str
    name: str
    code: str
    category: Optional[str] = None
    severity: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
