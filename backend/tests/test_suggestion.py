"""备货建议接口测试。"""
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.db import Base, SessionLocal, engine
from app.core.seed import seed_default_settings, seed_promotion_calendar, seed_sku_master
from app.datasources import registry
from app.engine.pipeline import run_calc
from app.main import app

MOCK = Path(__file__).resolve().parents[2] / "mock"


def _load_and_calc(db):
    seed_sku_master(db)
    seed_default_settings(db)
    seed_promotion_calendar(db, use_csv=True)
    for src in ["amazon_orders", "walmart_orders", "inventory_snapshot", "competitor", "trends", "env_score"]:
        registry.run(src, db, str(MOCK / f"{src}.csv"))
    db.commit()
    run_calc(db)


def test_suggestions_sorted_and_fields():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _load_and_calc(db)
    finally:
        db.close()
    with TestClient(app) as client:
        resp = client.get("/api/suggestions")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 8
    scores = [d["score"] for d in data]
    assert scores == sorted(scores, reverse=True)
    first = data[0]
    for k in ["sku", "name", "platform", "forecast_daily", "sellable_days", "suggest_qty", "score", "reason_text"]:
        assert k in first


def test_put_suggestion_adjust():
    with TestClient(app) as client:
        resp = client.put("/api/suggestions/SK-1023", json={"adjusted_qty": 500, "note": "人工加量"})
        assert resp.status_code == 200
        data = client.get("/api/suggestions").json()["data"]
        row = next(d for d in data if d["sku"] == "SK-1023")
        assert row["is_adjusted"] is True
        assert row["effective_qty"] == 500


def test_export_xlsx():
    with TestClient(app) as client:
        resp = client.get("/api/suggestions/export")
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers.get("content-type", "")
