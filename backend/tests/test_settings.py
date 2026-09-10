"""通用业务参数设置测试。"""
from fastapi.testclient import TestClient

from app.main import app


def test_settings_get_and_put():
    with TestClient(app) as client:
        r = client.get("/api/settings")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "base_weights" in data and "monthly_budget" in data

        r = client.put("/api/settings", json={"monthly_budget": 999999})
        assert r.status_code == 200
        assert r.json()["data"]["monthly_budget"] == 999999

        r = client.put("/api/settings", json={"base_weights": {"30d": 0.6, "90d": 0.3, "yoy": 0.1}})
        assert r.status_code == 200
        assert r.json()["data"]["base_weights"]["30d"] == 0.6
