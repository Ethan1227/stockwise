"""预警中心测试。"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.db import Base, SessionLocal, engine
from app.core.seed import seed_default_settings, seed_promotion_calendar, seed_sku_master
from app.datasources import registry
from app.engine.pipeline import run_calc
from app.main import app
from app.services.alert import scan_alerts

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
    scan_alerts(db)
    db.close()
    yield


def test_stockout_alerts():
    with TestClient(app) as client:
        data = client.get("/api/alerts", params={"type": "缺货"}).json()["data"]
    assert len(data) >= 3
    sk2087 = [a for a in data if a["sku"] == "SK-2087"]
    assert sk2087 and sk2087[0]["level"] == "紧急"


def test_slow_alerts():
    with TestClient(app) as client:
        data = client.get("/api/alerts", params={"type": "滞销"}).json()["data"]
    skus = {a["sku"] for a in data}
    assert "SK-0561" in skus and "SK-8830" in skus


def test_no_duplicate_alerts():
    with TestClient(app) as client:
        before = len(client.get("/api/alerts").json()["data"])
        client.post("/api/calc/run")
        after = len(client.get("/api/alerts").json()["data"])
    assert before == after


def test_change_threshold_increases():
    with TestClient(app) as client:
        before = len(client.get("/api/alerts").json()["data"])
        client.put("/api/settings/rules", json={"slow_mild_turnover": 30})
        client.post("/api/calc/run")
        after = len(client.get("/api/alerts").json()["data"])
    assert after > before
