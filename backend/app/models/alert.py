"""预警表 alert。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Alert(Base):
    __tablename__ = "alert"
    # 去重在应用层实现（扫描时跳过已存在的未处理同码预警），表上仅建组合索引
    __table_args__ = (Index("ix_alert_sku_code", "sku", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(32), default="")          # 规则码
    alert_type: Mapped[str] = mapped_column(String(16), default="")    # 缺货 / 滞销
    level: Mapped[str] = mapped_column(String(16), default="")         # 紧急 / 一般 / 严重 / 轻度
    title: Mapped[str] = mapped_column(String(128), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    advice: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="未处理")   # 未处理 / 已处理 / 已忽略
    notify_log: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
