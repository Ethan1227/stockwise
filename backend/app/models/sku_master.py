"""商品档案表 sku_master。"""
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SkuMaster(Base):
    __tablename__ = "sku_master"

    sku: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), default="")       # 亚马逊/沃尔玛/双平台
    category: Mapped[str] = mapped_column(String(64), default="")
    supplier: Mapped[str] = mapped_column(String(128), default="")
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    moq: Mapped[int] = mapped_column(Integer, default=1)               # 最小起订量
    lead_prod_days: Mapped[int] = mapped_column(Integer, default=0)    # 生产天数
    lead_ship_days: Mapped[int] = mapped_column(Integer, default=35)   # 头程天数
    safety_days: Mapped[int] = mapped_column(Integer, default=10)      # 安全天数
