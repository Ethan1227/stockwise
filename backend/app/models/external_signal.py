"""外部信号表 external_signals（trend/competitor/event/env）。

说明：竞品(competitor)一个 SKU 同期可有多条（一竞品一条），故不设 (sku,type,period) 唯一约束；
幂等由导入适配器「按 source+period 删除后重插」实现。env 为类目级信号，sku 字段存类目名。
"""
from sqlalchemy import Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ExternalSignal(Base):
    __tablename__ = "external_signals"
    __table_args__ = (Index("ix_ext_signal_sku_type", "sku", "signal_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # SKU 或类目名（env）
    signal_type: Mapped[str] = mapped_column(String(16), nullable=False)      # trend/competitor/event/env
    value_num: Mapped[float | None] = mapped_column(Float, nullable=True)     # 数值（如趋势变化 %、env 分数）
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)       # 文本/JSON（如竞品明细、备注）
    period: Mapped[str] = mapped_column(String(32), default="")               # 周期（如 2026-W37）
    source: Mapped[str] = mapped_column(String(32), default="")               # 来源（competitor/trends/env_score）
