"""智能问答测试。"""
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


def _chat(client, text):
    return client.post("/api/chat", json={"text": text}).json()["data"]


def test_replenish():
    with TestClient(app) as client:
        data = _chat(client, "本周要补什么货？")
    assert "SK-" in data["answer_md"]
    assert data["data_chips"]


def test_stockout_sk2087():
    with TestClient(app) as client:
        data = _chat(client, "SK-2087 会断货吗？")
    assert "SK-2087" in data["answer_md"]
    assert "空运" in data["answer_md"]


def test_slow_sk0561():
    with TestClient(app) as client:
        data = _chat(client, "哪些产品滞销？")
    assert "SK-0561" in data["answer_md"]


def test_generate_po_creates_draft():
    with TestClient(app) as client:
        before = len(client.get("/api/purchase-orders").json()["data"])
        _chat(client, "生成采购计划")
        after = len(client.get("/api/purchase-orders").json()["data"])
    assert after > before


def test_fallback():
    with TestClient(app) as client:
        data = _chat(client, "今天天气怎么样？")
    assert data["suggestions"]


def test_chat_llm_field_present():
    """回答体包含 llm 标记（deepseek-v4-flash 命中 或 fallback 兜底）。"""
    with TestClient(app) as client:
        data = _chat(client, "本周要补什么货？")
    assert data["llm"] in ("deepseek-v4-flash", "fallback")
