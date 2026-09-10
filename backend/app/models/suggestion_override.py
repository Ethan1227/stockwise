"""人工改量/忽略表 suggestion_override（每 SKU 每测算期一条）。"""
from datetime import date

from sqlalchemy import Date, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SuggestionOverride(Base):
    __tablename__ = "suggestion_override"
    __table_args__ = (UniqueConstraint("sku", "calc_date", name="uq_suggestion_override_sku_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    calc_date: Mapped[date] = mapped_column(Date, nullable=False)
    adjusted_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 人工改量（None=忽略）
    adjusted_by: Mapped[str] = mapped_column(String(64), default="")
    note: Mapped[str] = mapped_column(Text, default="")
