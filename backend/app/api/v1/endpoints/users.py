# -*- coding: utf-8 -*-
"""
Users API Endpoints
用户管理API端点
"""
import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_password_hash, get_current_user, require_admin
from app.core.exceptions import (
    UserNotFoundError,
    UsernameAlreadyExistsError,
    EmailAlreadyExistsError,
    RoleNotFoundError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.models.user import User, Organization
from app.models.rbac import Role, Permission, RolePermission
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserResetPassword, AssignRoleRequest,
    RoleCreate, RoleUpdate, RoleResponse, PermissionResponse,
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
)
from app.schemas.common import ResponseBase, DataResponse, PaginatedResponse, PaginationMeta
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[UserListResponse], summary="获取用户列表")
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    role_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).options(selectinload(User.role), selectinload(User.organization))
    count_query = select(func.count(User.id))

    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if role_id:
        query = query.where(User.role_id == role_id)
        count_query = count_query.where(User.role_id == role_id)

    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    user_list = [
        UserListResponse(
            id=str(u.id),
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            is_active=u.is_active,
            role_name=u.role.display_name if u.role else None,
            organization_name=u.organization.name if u.organization else None,
            created_at=u.created_at,
            last_login_at=u.last_login_at,
        )
        for u in users
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=user_list,
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages, has_prev=page > 1,
        ),
    )


@router.post("", response_model=DataResponse[UserResponse], summary="创建用户")
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Check username
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise UsernameAlreadyExistsError(user_data.username)

    # Check email
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise EmailAlreadyExistsError(user_data.email)

    user = User(
        id=uuid.uuid4(),
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role_id=user_data.role_id,
        organization_id=user_data.organization_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await AuditService.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="create",
        resource_type="user",
        resource_id=str(user.id),
        description=f"创建用户 {user.username}",
        request=request,
    )

    return DataResponse(
        data=UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
        )
    )


@router.get("/roles", response_model=DataResponse[list], summary="获取角色列表")
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Role).order_by(Role.created_at))
    roles = result.scalars().all()
    role_list = [
        RoleResponse(
            id=str(r.id), name=r.name, display_name=r.display_name,
            description=r.description, is_active=r.is_active,
            is_system=r.is_system, created_at=r.created_at,
        ).model_dump()
        for r in roles
    ]
    return DataResponse(data=role_list)


@router.get("/organizations", response_model=DataResponse[list], summary="获取组织列表")
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).order_by(Organization.created_at))
    orgs = result.scalars().all()
    org_list = [
        OrganizationResponse(
            id=str(o.id), name=o.name, code=o.code,
            description=o.description, is_active=o.is_active,
            created_at=o.created_at,
        ).model_dump()
        for o in orgs
    ]
    return DataResponse(data=org_list)
