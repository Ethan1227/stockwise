"""测算结果表 calc_result（不可变每日快照，唯一测算结果出口）。"""
from datetime import date

from sqlalchemy import JSON, Date, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CalcResult(Base):
    __tablename__ = "calc_result"
    __table_args__ = (UniqueConstraint("sku", "calc_date", name="uq_calc_result_sku_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    calc_date: Mapped[date] = mapped_column(Date, nullable=False)
    base_daily: Mapped[float] = mapped_column(Float, default=0.0)          # 基线日销
    forecast_daily: Mapped[float] = mapped_column(Float, default=0.0)      # 预测日销
    score: Mapped[int] = mapped_column(Integer, default=0)                 # 备货评分 0~100
    score_band: Mapped[str] = mapped_column(String(16), default="")        # 立即补货/常规/观望/停止补货
    suggest_qty: Mapped[int] = mapped_column(Integer, default=0)           # 建议备货量
    sellable_days: Mapped[float] = mapped_column(Float, default=0.0)       # 可售天数
    factors_json: Mapped[dict] = mapped_column(JSON, default=dict)         # 各修正器系数
    score_detail_json: Mapped[dict] = mapped_column(JSON, default=dict)    # 评分四维度明细
    reason_text: Mapped[str] = mapped_column(Text, default="")             # 人话依据
    data_flags: Mapped[dict] = mapped_column(JSON, default=dict)           # 数据降级标记
