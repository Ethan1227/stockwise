"""商品档案（sku_master）Pydantic 模型。"""
from pydantic import BaseModel


class SkuCreate(BaseModel):
    sku: str
    name: str
    platform: str = ""
    category: str = ""
    supplier: str = ""
    unit_cost: float = 0.0
    price: float = 0.0
    moq: int = 1
    lead_prod_days: int = 0
    lead_ship_days: int = 35
    safety_days: int = 10


class SkuUpdate(BaseModel):
    name: str | None = None
    platform: str | None = None
    category: str | None = None
    supplier: str | None = None
    unit_cost: float | None = None
    price: float | None = None
    moq: int | None = None
    lead_prod_days: int | None = None
    lead_ship_days: int | None = None
    safety_days: int | None = None
