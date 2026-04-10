# -*- coding: utf-8 -*-
"""
Custom Exceptions
自定义异常
"""
from fastapi import HTTPException, status


class AppException(HTTPException):
    """应用基础异常"""

    def __init__(self, status_code: int, error_code: str, message: str, detail: str = None):
        self.error_code = error_code
        self.message = message
        self.detail = detail
        super().__init__(status_code=status_code, detail=message)


class InvalidCredentialsError(AppException):
    def __init__(self, detail: str = "用户名或密码错误"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", detail)


class InvalidTokenError(AppException):
    def __init__(self, detail: str = "无效的令牌"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", detail)


class UserNotFoundError(AppException):
    def __init__(self, identifier: str = ""):
        super().__init__(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", f"用户不存在: {identifier}")


class UserDisabledError(AppException):
    def __init__(self, username: str = ""):
        super().__init__(status.HTTP_403_FORBIDDEN, "USER_DISABLED", f"用户已被禁用: {username}")


class UsernameAlreadyExistsError(AppException):
    def __init__(self, username: str = ""):
        super().__init__(status.HTTP_409_CONFLICT, "USERNAME_EXISTS", f"用户名已存在: {username}")


class EmailAlreadyExistsError(AppException):
    def __init__(self, email: str = ""):
        super().__init__(status.HTTP_409_CONFLICT, "EMAIL_EXISTS", f"邮箱已被使用: {email}")


class RoleNotFoundError(AppException):
    def __init__(self, identifier: str = ""):
        super().__init__(status.HTTP_404_NOT_FOUND, "ROLE_NOT_FOUND", f"角色不存在: {identifier}")


class PermissionDeniedError(AppException):
    def __init__(self, detail: str = "权限不足"):
        super().__init__(status.HTTP_403_FORBIDDEN, "PERMISSION_DENIED", detail)


class ResourceNotFoundError(AppException):
    def __init__(self, resource_type: str = "资源", identifier: str = ""):
        super().__init__(status.HTTP_404_NOT_FOUND, "RESOURCE_NOT_FOUND", f"{resource_type}不存在: {identifier}")


class DeviceNotFoundError(AppException):
    def __init__(self, identifier: str = ""):
        super().__init__(status.HTTP_404_NOT_FOUND, "DEVICE_NOT_FOUND", f"设备不存在: {identifier}")


class ValidationError(AppException):
    def __init__(self, detail: str = "数据验证失败"):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", detail)
