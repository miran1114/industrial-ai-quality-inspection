# -*- coding: utf-8 -*-
"""
Industrial AI Platform - Main FastAPI Application
工业智能分析平台 - 主应用入口
"""
import logging
import time
import uuid

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.database import engine, Base, async_session_maker
from app.core.security import get_password_hash
from app.api.v1.router import api_router
from app.core.exceptions import AppException
from app.middleware.audit import AuditMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def init_default_data():
    """Initialize default roles and admin user"""
    from app.models.rbac import Role, Permission, RolePermission
    from app.models.user import User, Organization

    async with async_session_maker() as db:
        # Check if roles exist
        result = await db.execute(select(Role).where(Role.name == "superuser"))
        if result.scalar_one_or_none():
            return  # Already initialized

        # Create roles
        roles = [
            Role(id=uuid.uuid4(), name="superuser", display_name="超级管理员", is_system=True),
            Role(id=uuid.uuid4(), name="admin", display_name="管理员", is_system=True),
            Role(id=uuid.uuid4(), name="user", display_name="普通用户", is_system=True),
            Role(id=uuid.uuid4(), name="viewer", display_name="只读用户", is_system=True),
        ]
        for r in roles:
            db.add(r)
        await db.flush()

        # Create default organization
        org = Organization(
            id=uuid.uuid4(),
            name="默认组织",
            code="default",
            description="系统默认组织",
        )
        db.add(org)
        await db.flush()

        # Create admin user
        superuser_role = roles[0]
        admin_user = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("Admin@123456"),
            full_name="系统管理员",
            role_id=superuser_role.id,
            organization_id=org.id,
            is_active=True,
            is_verified=True,
        )
        db.add(admin_user)

        # Create permissions
        permission_codes = [
            ("user:read", "查看用户", "user"),
            ("user:write", "管理用户", "user"),
            ("device:read", "查看设备", "device"),
            ("device:write", "管理设备", "device"),
            ("defect:read", "查看缺陷", "defect"),
            ("defect:write", "管理缺陷", "defect"),
            ("timeseries:read", "查看时序", "timeseries"),
            ("timeseries:write", "管理时序", "timeseries"),
            ("system:admin", "系统管理", "system"),
        ]
        permissions = []
        for code, name, module in permission_codes:
            p = Permission(id=uuid.uuid4(), name=name, code=code, module=module)
            db.add(p)
            permissions.append(p)
        await db.flush()

        # Assign all permissions to superuser role
        for p in permissions:
            rp = RolePermission(id=uuid.uuid4(), role_id=superuser_role.id, permission_id=p.id)
            db.add(rp)

        await db.commit()
        logger.info("Default data initialized: admin/Admin@123456")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Industrial AI Platform...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_default_data()
    yield
    logger.info("Shutting down Industrial AI Platform...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="半导体光伏缺陷智能诊断与时序分析系统 - 支持缺陷诊断、时序分析、设备健康管理",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit middleware
app.add_middleware(AuditMiddleware)


# Process time middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


# Register routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "message": "Welcome to Industrial AI Platform",
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }
