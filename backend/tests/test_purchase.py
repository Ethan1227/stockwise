"""采购计划测试。"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.db import Base, SessionLocal, engine
from app.core.seed import seed_default_settings, seed_promotion_calendar, seed_sku_master
from app.datasources import registry
from app.engine.pipeline import run_calc
from app.main import app
from app.models.inventory_snapshot import InventorySnapshot
from app.models.setting import Setting

MOCK = Path(__file__).resolve().parents[2] / "mock"


def _load(db):
    seed_sku_master(db)
    seed_default_settings(db)
    seed_promotion_calendar(db, use_csv=True)
    for src in ["amazon_orders", "walmart_orders", "inventory_snapshot", "competitor", "trends", "env_score"]:
        registry.run(src, db, str(MOCK / f"{src}.csv"))
    db.commit()


@pytest.fixture(scope="module", autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    _load(db)
    run_calc(db)
    db.close()
    yield


def _inv(sku: str) -> InventorySnapshot:
    db = SessionLocal()
    try:
        return db.query(InventorySnapshot).filter_by(sku=sku).order_by(InventorySnapshot.date.desc()).first()
    finally:
        db.close()


def test_generate_grouped():
    with TestClient(app) as client:
        r = client.post("/api/purchase-orders/generate", json={"skus": ["SK-1023", "SK-2087", "SK-4419"]})
    assert r.status_code == 200
    orders = r.json()["data"]
    assert len(orders) == 2
    assert {o["supplier"] for o in orders} == {"义乌XX宠物用品", "深圳XX家居"}


def test_confirm_ship_arrive_flow():
    with TestClient(app) as client:
        r = client.post("/api/purchase-orders/generate", json={"skus": ["SK-2087"]})
        po = r.json()["data"][0]
        po_id = po["id"]
        qty = po["total_qty"]

        before = _inv("SK-2087")
        client.put(f"/api/purchase-orders/{po_id}/confirm")
        after_confirm = _inv("SK-2087")
        assert after_confirm.in_transit_qty == before.in_transit_qty + qty

        client.put(f"/api/purchase-orders/{po_id}/ship")
        client.put(f"/api/purchase-orders/{po_id}/arrive")
        after_arrive = _inv("SK-2087")
        assert after_arrive.in_transit_qty == before.in_transit_qty
        assert after_arrive.wfs_qty == before.wfs_qty + qty


def test_budget_warning():
    db = SessionLocal()
    s = db.get(Setting, "monthly_budget")
    s.value = 1
    db.commit()
    db.close()
    with TestClient(app) as client:
        r = client.post("/api/purchase-orders/generate", json={"skus": ["SK-1023"]})
    po = r.json()["data"][0]
    assert "budget" in po["warning"]


def test_export_xlsx():
    with TestClient(app) as client:
        r = client.post("/api/purchase-orders/generate", json={"skus": ["SK-1023"]})
        po_id = r.json()["data"][0]["id"]
        exp = client.get(f"/api/purchase-orders/{po_id}/export")
    assert exp.status_code == 200
    assert "spreadsheetml" in exp.headers.get("content-type", "")


def test_manual_order():
    with TestClient(app) as client:
        r = client.post("/api/purchase-orders/manual", json={
            "supplier": "测试供应商",
            "dest_warehouse": "FBA",
            "status": "shipped",
            "items": [{"sku": "SK-1023", "qty": 100, "unit_cost": 6.5}],
        })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "shipped"
    assert data["total_qty"] == 100
    assert data["items"][0]["sku"] == "SK-1023"
