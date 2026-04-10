# -*- coding: utf-8 -*-
"""
Timeseries Models
时序分析模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base, GUID


class TimeseriesDataset(Base):
    """时序数据集表"""
    __tablename__ = "timeseries_datasets"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    source_type = Column(String(50), default="upload")
    file_path = Column(String(500), nullable=True)

    device_id = Column(GUID(), ForeignKey("devices.id"), nullable=True)
    device = relationship("Device", back_populates="timeseries_datasets")

    data_type = Column(String(50), nullable=True)
    sampling_rate = Column(Float, nullable=True)
    total_points = Column(Integer, default=0)

    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    extra_data = Column(JSON, nullable=True)
    columns_config = Column(JSON, nullable=True)

    created_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    creator = relationship("User", back_populates="timeseries_datasets")

    status = Column(String(20), default="active")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    data_points = relationship("TimeseriesPoint", back_populates="dataset", cascade="all, delete-orphan")
    anomalies = relationship("TimeseriesAnomaly", back_populates="dataset", cascade="all, delete-orphan")
    reports = relationship("AnalysisReport", back_populates="dataset")

    def __repr__(self):
        return f"<TimeseriesDataset {self.name}>"


class TimeseriesPoint(Base):
    """时序数据点表"""
    __tablename__ = "timeseries_points"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(GUID(), ForeignKey("timeseries_datasets.id"), nullable=False)
    dataset = relationship("TimeseriesDataset", back_populates="data_points")

    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=True)
    values = Column(JSON, nullable=True)
    quality = Column(Integer, default=100)
    extra_data = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<TimeseriesPoint {self.timestamp}>"


class TimeseriesAnomaly(Base):
    """时序异常表"""
    __tablename__ = "timeseries_anomalies"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    dataset_id = Column(GUID(), ForeignKey("timeseries_datasets.id"), nullable=False)
    dataset = relationship("TimeseriesDataset", back_populates="anomalies")

    anomaly_type = Column(String(50), nullable=True)
    severity = Column(String(20), default="medium")

    timestamp = Column(DateTime, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)

    value = Column(Float, nullable=True)
    score = Column(Float, default=0.0)
    threshold = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    detection_method = Column(String(50), nullable=True)

    details = Column(JSON, nullable=True)
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)

    status = Column(String(20), default="detected")
    is_confirmed = Column(Boolean, default=False)
    is_false_positive = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TimeseriesAnomaly {self.anomaly_type} at {self.start_time}>"


class AnalysisReport(Base):
    """分析报告表"""
    __tablename__ = "analysis_reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    report_type = Column(String(50), default="timeseries")
    description = Column(Text, nullable=True)

    content_json = Column(JSON, nullable=True)
    content_markdown = Column(Text, nullable=True)

    dataset_id = Column(GUID(), ForeignKey("timeseries_datasets.id"), nullable=True)
    dataset = relationship("TimeseriesDataset", back_populates="reports")

    device_id = Column(GUID(), nullable=True)
    job_id = Column(GUID(), nullable=True)
    export_path = Column(String(500), nullable=True)

    created_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    creator = relationship("User", back_populates="analysis_reports")

    status = Column(String(20), default="draft")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AnalysisReport {self.title}>"
