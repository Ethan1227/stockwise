"""数据导入接口测试。"""
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

MOCK = Path(__file__).resolve().parents[2] / "mock"


def _upload(client, source: str, path: Path):
    with open(path, "rb") as f:
        return client.post(f"/api/import/{source}", files={"file": (path.name, f, "text/csv")})


def test_import_amazon_orders():
    with TestClient(app) as client:
        resp = _upload(client, "amazon_orders", MOCK / "amazon_orders.csv")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["written"] == 696  # 697 行 - 1 表头


def test_import_walmart_orders():
    with TestClient(app) as client:
        resp = _upload(client, "walmart_orders", MOCK / "walmart_orders.csv")
    assert resp.status_code == 200
    assert resp.json()["data"]["written"] == 348


def test_import_inventory_idempotent():
    with TestClient(app) as client:
        first = _upload(client, "inventory_snapshot", MOCK / "inventory_snapshot.csv")
        assert first.status_code == 200
        assert first.json()["data"]["written"] == 8
        # 重复导入行数不变
        second = _upload(client, "inventory_snapshot", MOCK / "inventory_snapshot.csv")
        assert second.status_code == 200
        assert second.json()["data"]["written"] == 8


def test_import_missing_column_returns_400():
    bad = "sku,date\nSK-1,2026-01-01\n".encode("utf-8")
    with TestClient(app) as client:
        resp = client.post(
            "/api/import/amazon_orders",
            files={"file": ("bad.csv", bad, "text/csv")},
        )
    assert resp.status_code == 400


def test_list_datasources_returns_six():
    with TestClient(app) as client:
        resp = client.get("/api/datasources")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 6
    assert {d["source_code"] for d in data} == {
        "amazon_orders",
        "walmart_orders",
        "inventory_snapshot",
        "competitor",
        "trends",
        "env_score",
    }
