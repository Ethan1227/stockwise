"""外部信号表 external_signals（trend/competitor/event/env）。"""
from sqlalchemy import Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ExternalSignal(Base):
    __tablename__ = "external_signals"
    __table_args__ = (UniqueConstraint("sku", "signal_type", "period", name="uq_ext_signal_sku_type_period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    signal_type: Mapped[str] = mapped_column(String(16), nullable=False)   # trend/competitor/event/env
    value_num: Mapped[float | None] = mapped_column(Float, nullable=True)  # 数值（如趋势变化 %）
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)    # 文本（如竞品状态）
    period: Mapped[str] = mapped_column(String(32), default="")            # 周期（如 2026-W37）
    source: Mapped[str] = mapped_column(String(32), default="")            # 来源（competitor/trends/env_score）
