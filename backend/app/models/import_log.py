"""导入审计日志表 import_log（操作表，不计入 9 张领域表）。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ImportLog(Base):
    __tablename__ = "import_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(256), default="")
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    success_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_detail: Mapped[dict] = mapped_column(JSON, default=dict)   # 行级错误明细
    operator: Mapped[str] = mapped_column(String(64), default="")   # 操作人
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
