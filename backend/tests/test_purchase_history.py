"""历史采购单回填测试。"""
from pathlib import Path

from app.core.db import Base, SessionLocal, engine
from app.core.seed import seed_default_settings, seed_promotion_calendar, seed_sku_master
from app.datasources import registry
from app.models.inventory_snapshot import InventorySnapshot
from app.models.purchase_order import PurchaseOrder
from app.services.purchase_history import import_purchase_history

MOCK = Path(__file__).resolve().parents[2] / "mock"


def test_import_purchase_history():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_sku_master(db)
        seed_default_settings(db)
        seed_promotion_calendar(db, use_csv=True)
        registry.run("inventory_snapshot", db, str(MOCK / "inventory_snapshot.csv"))
        db.commit()

        before_val = db.query(InventorySnapshot).filter_by(sku="SK-2087").order_by(InventorySnapshot.date.desc()).first().in_transit_qty
        n = import_purchase_history(db, str(MOCK / "purchase_orders_history.csv"))
        db.commit()

        assert n == 2
        imported = db.query(PurchaseOrder).filter(PurchaseOrder.po_no.in_(["PO-20260810-01", "PO-20260815-01"])).all()
        assert len(imported) == 2
        assert {po.status for po in imported} == {"shipped", "arrived"}

        after_val = db.query(InventorySnapshot).filter_by(sku="SK-2087").order_by(InventorySnapshot.date.desc()).first().in_transit_qty
        # shipped 的 SK-2087 400 件应计入在途
        assert after_val == before_val + 400
    finally:
        db.close()
