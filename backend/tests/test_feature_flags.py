"""功能开关测试。"""
from fastapi.testclient import TestClient

from app.main import app


def test_feature_flags_toggle():
    with TestClient(app) as client:
        # 默认全开
        r = client.get("/api/settings/flags")
        assert r.status_code == 200
        assert r.json()["data"].get("alert", True) is True

        # 关闭预警中心
        r = client.put("/api/settings/flags", json={"alert": False})
        assert r.status_code == 200
        assert r.json()["data"]["alert"] is False

        # 预警接口应返回 403
        assert client.get("/api/alerts").status_code == 403

        # 其它功能不受影响
        assert client.get("/api/suggestions").status_code == 200

        # 重新开启后恢复
        client.put("/api/settings/flags", json={"alert": True})
        assert client.get("/api/alerts").status_code == 200
