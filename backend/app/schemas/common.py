# -*- coding: utf-8 -*-
"""
Common Schemas
通用响应模型
"""
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel
from datetime import datetime

T = TypeVar("T")


class ResponseBase(BaseModel):
    success: bool = True
    message: str = "操作成功"


class DataResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = "操作成功"


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    meta: PaginationMeta
