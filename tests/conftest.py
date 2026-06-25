from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    id: int
    sku: str = Field(min_length=1)


class OrderResult(BaseModel):
    id: int
    status: str


class StatusEnum(str, Enum):
    OK = "ok"
    FAIL = "fail"


class UnsupportedClass:
    pass
