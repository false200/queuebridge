from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    id: int
    sku: str = Field(min_length=1)


class OrderResult(BaseModel):
    id: int
    status: str
