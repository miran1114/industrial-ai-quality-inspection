# -*- coding: utf-8 -*-
"""
Auth API Endpoints
认证API端点
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    verify_password_reset_token,
    get_current_user,
)
from app.core.config import settings
from app.core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserNotFoundError,
    UsernameAlreadyExistsError,
    EmailAlreadyExistsError,
)
from app.models.user import User
from app.models.rbac import Role
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    UserInfo,
)
from app.schemas.common import ResponseBase, DataResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/login", response_model=DataResponse[TokenResponse], summary="用户登录")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise InvalidCredentialsError("用户已被禁用")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    user.last_login_at = datetime.utcnow()
    await db.commit()

    await AuditService.log(
        db=db,
        user_id=user.id,
        username=user.username,
        action="login",
        resource_type="auth",
        description=f"用户 {user.username} 登录",
        request=request,
    )

    return DataResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    )


@router.post("/register", response_model=DataResponse[TokenResponse], summary="用户注册")
async def register(
    request: Request,
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    # Check username
    result = await db.execute(select(User).where(User.username == register_data.username))
    if result.scalar_one_or_none():
        raise UsernameAlreadyExistsError(register_data.username)

    # Check email
    result = await db.execute(select(User).where(User.email == register_data.email))
    if result.scalar_one_or_none():
        raise EmailAlreadyExistsError(register_data.email)

    # Get default role
    role_result = await db.execute(select(Role).where(Role.name == "user"))
    default_role = role_result.scalar_one_or_none()

    user = User(
        id=uuid.uuid4(),
        username=register_data.username,
        email=register_data.email,
        hashed_password=get_password_hash(register_data.password),
        full_name=register_data.full_name,
        phone=register_data.phone,
        role_id=default_role.id if default_role else None,
        is_active=True,
    )
    db.add(user)
    await db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    await AuditService.log(
        db=db,
        user_id=user.id,
        username=user.username,
        action="register",
        resource_type="auth",
        description=f"用户 {user.username} 注册",
        request=request,
    )

    return DataResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    )


@router.post("/logout", response_model=ResponseBase, summary="用户登出")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await AuditService.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="logout",
        resource_type="auth",
        description=f"用户 {current_user.username} 登出",
        request=request,
    )
    return ResponseBase(message="登出成功")


@router.post("/password/reset", response_model=ResponseBase, summary="请求密码重置")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == reset_request.email))
    user = result.scalar_one_or_none()
    if user:
        reset_token = create_password_reset_token(user.email)
        print(f"Password reset token for {user.email}: {reset_token}")
    return ResponseBase(message="如果邮箱存在，重置链接已发送")


@router.post("/password/reset/confirm", response_model=ResponseBase, summary="确认密码重置")
async def confirm_password_reset(
    confirm_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    email = verify_password_reset_token(confirm_data.token)
    if not email:
        raise InvalidTokenError("无效或过期的重置令牌")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundError(email)

    user.hashed_password = get_password_hash(confirm_data.new_password)
    await db.commit()
    return ResponseBase(message="密码重置成功")


@router.post("/password/change", response_model=ResponseBase, summary="修改密码")
async def change_password(
    request: Request,
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(change_data.old_password, current_user.hashed_password):
        raise InvalidCredentialsError("旧密码错误")

    current_user.hashed_password = get_password_hash(change_data.new_password)
    await db.commit()

    await AuditService.log(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="change_password",
        resource_type="user",
        resource_id=str(current_user.id),
        description=f"用户 {current_user.username} 修改密码",
        request=request,
    )
    return ResponseBase(message="密码修改成功")


@router.get("/me", response_model=DataResponse[UserInfo], summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    permissions = []
    if current_user.role:
        for rp in current_user.role.role_permissions:
            permissions.append(rp.permission.code)

    user_info = UserInfo(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        role_name=current_user.role.name if current_user.role else None,
        role_display_name=current_user.role.display_name if current_user.role else None,
        organization_name=current_user.organization.name if current_user.organization else None,
        permissions=permissions,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )
    return DataResponse(data=user_info)
