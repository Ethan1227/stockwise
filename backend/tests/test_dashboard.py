"""工作台聚合测试。"""
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


def test_summary():
    with TestClient(app) as client:
        data = client.get("/api/dashboard/summary").json()["data"]
    assert data["kpi"]["sku_count"] == 8
    assert data["kpi"]["stockout"] >= 3
    assert len(data["datasources"]) == 6
    assert data["sales_series"]
    # 待办含黑五倒计时
    todo_types = [t["type"] for t in data["todos"]]
    assert "大促" in todo_types
    black_friday = next(t for t in data["todos"] if t["type"] == "大促")
    assert "倒计时" in black_friday["text"]


def test_calc_history():
    with TestClient(app) as client:
        r = client.get("/api/calc/history")
        assert r.status_code == 200
        dates = r.json()["data"]
        assert len(dates) >= 1
        assert dates[0]["count"] == 8

        r = client.get("/api/calc/history/SK-2087")
        assert r.status_code == 200
        rows = r.json()["data"]
        assert len(rows) >= 1
        assert "forecast_daily" in rows[0] and "score" in rows[0]
