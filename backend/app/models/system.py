# -*- coding: utf-8 -*-
"""
System Models
系统模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid

from app.core.database import Base, GUID


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisJob(Base):
    """分析任务表"""
    __tablename__ = "analysis_jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    job_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    config = Column(JSON, nullable=True)
    input_params = Column(JSON, nullable=True)

    status = Column(String(20), default="pending")
    progress = Column(Float, default=0.0)

    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    dataset_id = Column(GUID(), nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    created_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    creator = relationship("User", back_populates="analysis_jobs")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AnalysisJob {self.name} status={self.status}>"


class Notification(Base):
    """通知表"""
    __tablename__ = "notifications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    notification_type = Column(String(50), default="info")

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="notifications")

    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    related_type = Column(String(50), nullable=True)
    related_id = Column(GUID(), nullable=True)
    extra_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.title}>"


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="audit_logs")
    username = Column(String(100), nullable=True)

    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    details = Column(JSON, nullable=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)

    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username}>"
