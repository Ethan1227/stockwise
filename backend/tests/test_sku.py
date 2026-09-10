"""商品档案 CRUD 测试。"""
from fastapi.testclient import TestClient

from app.main import app


def test_sku_crud():
    with TestClient(app) as client:
        r = client.post("/api/skus", json={"sku": "SK-TEST", "name": "测试商品", "platform": "亚马逊", "moq": 100})
        assert r.status_code == 200
        assert r.json()["data"]["sku"] == "SK-TEST"

        r = client.put("/api/skus/SK-TEST", json={"price": 99.9})
        assert r.status_code == 200
        assert r.json()["data"]["price"] == 99.9

        r = client.get("/api/skus")
        assert any(s["sku"] == "SK-TEST" for s in r.json()["data"])

        r = client.delete("/api/skus/SK-TEST")
        assert r.status_code == 200

        r = client.get("/api/skus")
        assert not any(s["sku"] == "SK-TEST" for s in r.json()["data"])


def test_create_duplicate_sku_400():
    with TestClient(app) as client:
        client.post("/api/skus", json={"sku": "SK-DUP", "name": "重复"})
        r = client.post("/api/skus", json={"sku": "SK-DUP", "name": "重复2"})
        assert r.status_code == 400
        client.delete("/api/skus/SK-DUP")  # 清理，避免污染其它测试
