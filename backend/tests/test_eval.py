"""评测指标测试。"""
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


def test_eval_metrics():
    with TestClient(app) as client:
        r = client.get("/api/eval/metrics")
    assert r.status_code == 200
    data = r.json()["data"]
    assert {"intent", "stockout", "slow", "score_band", "suggest"} <= set(data.keys())
    # 意图识别（关键词路由确定性）应 100% 准确
    assert data["intent"]["accuracy"] == 1.0
    # 断货/滞销预警应高准确率
    assert data["stockout"]["accuracy"] >= 0.8
    assert data["slow"]["accuracy"] >= 0.8
    # 各指标字段齐全
    for k in ["accuracy", "precision", "recall", "f1"]:
        assert k in data["intent"]
