"""日销售表 daily_sales（订单报表按平台聚合）。"""
from datetime import date

from sqlalchemy import Boolean, Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class DailySales(Base):
    __tablename__ = "daily_sales"
    __table_args__ = (UniqueConstraint("sku", "platform", "date", name="uq_daily_sales_sku_platform_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(16), nullable=False)   # amazon / walmart
    date: Mapped[date] = mapped_column(Date, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, default=0)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    is_stockout_day: Mapped[bool] = mapped_column(Boolean, default=False)  # 断货日（基线计算剔除）
