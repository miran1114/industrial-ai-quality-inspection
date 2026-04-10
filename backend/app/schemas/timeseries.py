# -*- coding: utf-8 -*-
"""
Timeseries Schemas
时序分析模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TimeseriesDatasetCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    device_id: Optional[str] = None
    sensor_name: Optional[str] = None
    parameter_name: Optional[str] = None
    unit: Optional[str] = None


class TimeseriesDatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    source_type: str = "upload"
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    sensor_name: Optional[str] = None
    parameter_name: Optional[str] = None
    unit: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    point_count: int = 0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    status: str = "active"
    uploaded_by: Optional[str] = None
    created_at: Optional[datetime] = None


class TimeseriesDatasetListResponse(BaseModel):
    id: str
    name: str
    device_name: Optional[str] = None
    sensor_name: Optional[str] = None
    point_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "active"
    created_at: Optional[datetime] = None


class TimeseriesPointResponse(BaseModel):
    timestamp: datetime
    value: float
    quality: int = 100


class TimeseriesDataResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    unit: Optional[str] = None
    points: List[TimeseriesPointResponse]
    statistics: Optional[Dict[str, Any]] = None


class SimulateDataRequest(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    device_id: Optional[str] = None
    sensor_name: str = "temperature"
    parameter_name: str = "温度"
    unit: str = "°C"
    start_time: datetime
    end_time: datetime
    frequency_seconds: int = Field(default=60, ge=1)
    base_value: float = 25.0
    trend_slope: float = 0.0
    noise_std: float = 1.0
    anomaly_ratio: float = Field(default=0.02, ge=0, le=1)


class TimeseriesAnalysisRequest(BaseModel):
    dataset_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    analysis_types: List[str] = ["statistics", "anomaly_detection"]
    anomaly_method: str = "zscore"
    anomaly_threshold: float = 3.0


class TriggerAnalysisResponse(BaseModel):
    job_id: str
    dataset_id: str
    message: str


class TimeseriesAnomalyResponse(BaseModel):
    id: str
    dataset_id: str
    timestamp: Optional[datetime] = None
    value: Optional[float] = None
    anomaly_type: Optional[str] = None
    severity: str = "medium"
    score: float = 0.0
    detection_method: Optional[str] = None
    threshold: Optional[float] = None
    description: Optional[str] = None
    is_confirmed: bool = False
    is_false_positive: bool = False
    created_at: Optional[datetime] = None


class AnalysisReportResponse(BaseModel):
    id: str
    title: str
    report_type: str
    description: Optional[str] = None
    content_json: Optional[Any] = None
    content_markdown: Optional[str] = None
    dataset_id: Optional[str] = None
    device_id: Optional[str] = None
    job_id: Optional[str] = None
    export_path: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
