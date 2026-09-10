"""采购计划相关 Pydantic 模型。"""
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    skus: list[str]


class ManualItem(BaseModel):
    sku: str
    qty: int
    unit_cost: float = 0.0


class ManualOrderRequest(BaseModel):
    supplier: str
    dest_warehouse: str = ""
    status: str = "draft"
    required_date: str | None = None
    items: list[ManualItem]
