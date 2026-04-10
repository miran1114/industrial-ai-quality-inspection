# -*- coding: utf-8 -*-
"""
Industrial Models
工业资产模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base, GUID


class ProductionLine(Base):
    """生产线表"""
    __tablename__ = "production_lines"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    status = Column(String(20), default="active")

    organization_id = Column(GUID(), ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="production_lines")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    devices = relationship("Device", back_populates="production_line")
    batches = relationship("Batch", back_populates="production_line")

    def __repr__(self):
        return f"<ProductionLine {self.name}>"


class Device(Base):
    """设备表"""
    __tablename__ = "devices"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    device_type = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)

    status = Column(String(20), default="online")
    health_score = Column(Float, default=100.0)

    production_line_id = Column(GUID(), ForeignKey("production_lines.id"), nullable=True)
    production_line = relationship("ProductionLine", back_populates="devices")

    config = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_maintenance_at = Column(DateTime, nullable=True)

    defect_samples = relationship("DefectSample", back_populates="device")
    timeseries_datasets = relationship("TimeseriesDataset", back_populates="device")

    def __repr__(self):
        return f"<Device {self.name}>"


class Batch(Base):
    """生产批次表"""
    __tablename__ = "batches"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    batch_no = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    product_type = Column(String(100), nullable=True)
    quantity = Column(Integer, default=0)
    status = Column(String(20), default="in_progress")

    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    production_line_id = Column(GUID(), ForeignKey("production_lines.id"), nullable=True)
    production_line = relationship("ProductionLine", back_populates="batches")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    defect_samples = relationship("DefectSample", back_populates="batch")

    def __repr__(self):
        return f"<Batch {self.batch_no}>"
