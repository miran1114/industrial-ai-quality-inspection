# -*- coding: utf-8 -*-
"""
Defect Models
缺陷检测模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base, GUID


class DefectType(Base):
    """缺陷类型表"""
    __tablename__ = "defect_types"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    category = Column(String(50), nullable=True)
    severity = Column(String(20), default="medium")
    description = Column(Text, nullable=True)
    detection_params = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    defect_results = relationship("DefectResult", back_populates="defect_type")

    def __repr__(self):
        return f"<DefectType {self.name}>"


class DefectSample(Base):
    """缺陷样本表"""
    __tablename__ = "defect_samples"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sample_no = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=True)
    sample_type = Column(String(50), nullable=True)

    file_path = Column(String(500), nullable=True)
    file_name = Column(String(200), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)

    source = Column(String(50), default="upload")

    device_id = Column(GUID(), ForeignKey("devices.id"), nullable=True)
    device = relationship("Device", back_populates="defect_samples")

    batch_id = Column(GUID(), ForeignKey("batches.id"), nullable=True)
    batch = relationship("Batch", back_populates="defect_samples")

    uploaded_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    uploaded_by_user = relationship("User", back_populates="defect_samples")

    status = Column(String(20), default="pending")
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    defect_results = relationship("DefectResult", back_populates="sample", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DefectSample {self.sample_no}>"


class DefectResult(Base):
    """缺陷检测结果表"""
    __tablename__ = "defect_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    sample_id = Column(GUID(), ForeignKey("defect_samples.id"), nullable=False)
    sample = relationship("DefectSample", back_populates="defect_results")

    defect_type_id = Column(GUID(), ForeignKey("defect_types.id"), nullable=True)
    defect_type = relationship("DefectType", back_populates="defect_results")

    has_defect = Column(Boolean, default=False)
    confidence = Column(Float, default=0.0)

    bbox = Column(JSON, nullable=True)
    mask = Column(JSON, nullable=True)
    analysis_details = Column(JSON, nullable=True)

    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DefectResult sample={self.sample_id} defect={self.has_defect}>"
