"""采购单表 purchase_order。"""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # PO-日期-序号
    supplier: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(16), default="draft")   # draft/confirmed/shipped/arrived
    total_qty: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    required_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # 要求到货日
    dest_warehouse: Mapped[str] = mapped_column(String(64), default="")
    items_json: Mapped[dict] = mapped_column(JSON, default=dict)
    suggest_air: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否建议改空运（交期倒排）
    warning: Mapped[dict] = mapped_column(JSON, default=dict)          # 预算/交期提醒
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
