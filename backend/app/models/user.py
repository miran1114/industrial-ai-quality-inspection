# -*- coding: utf-8 -*-
"""
User Model
用户模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base, GUID


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    role_id = Column(GUID(), ForeignKey("roles.id"), nullable=True)
    role = relationship("Role", back_populates="users")

    organization_id = Column(GUID(), ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="users")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    defect_samples = relationship("DefectSample", back_populates="uploaded_by_user")
    analysis_jobs = relationship("AnalysisJob", back_populates="creator")
    timeseries_datasets = relationship("TimeseriesDataset", back_populates="creator")
    analysis_reports = relationship("AnalysisReport", back_populates="creator")

    def __repr__(self):
        return f"<User {self.username}>"


class Organization(Base):
    """组织/租户表"""
    __tablename__ = "organizations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    production_lines = relationship("ProductionLine", back_populates="organization")

    def __repr__(self):
        return f"<Organization {self.name}>"
