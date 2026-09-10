"""库存快照表 inventory_snapshot（当日快照，幂等）。"""
from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshot"
    __table_args__ = (UniqueConstraint("sku", "date", name="uq_inventory_snapshot_sku_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    fba_qty: Mapped[int] = mapped_column(Integer, default=0)     # 亚马逊 FBA 可售
    wfs_qty: Mapped[int] = mapped_column(Integer, default=0)     # 沃尔玛 WFS 可售
    cn_qty: Mapped[int] = mapped_column(Integer, default=0)      # 国内仓可售
    in_transit_qty: Mapped[int] = mapped_column(Integer, default=0)  # 在途
    age_days: Mapped[int] = mapped_column(Integer, default=0)    # 库龄
