#!/usr/bin/env bash
set -euo pipefail
# 阶段 4 验收门：缺货预警 / 滞销预警 / 去重 / 阈值调整 / npm build

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PY="$ROOT/.venv/Scripts/python.exe"
[ -f "$PY" ] || PY="$ROOT/.venv/bin/python"

echo "=== 阶段 4 验收门 ==="

echo "[1/3] 重置数据库 + 导入 + 测算"
rm -f "$ROOT/data/stockwise.db"
(cd "$BACKEND" && "$PY" -m alembic upgrade head >/dev/null && "$PY" -m app.core.seed --mock >/dev/null)

(cd "$BACKEND" && "$PY" - <<'PYEOF'
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

MOCK = Path("../mock").resolve()
with TestClient(app) as client:
    for src in ["amazon_orders", "walmart_orders", "inventory_snapshot", "competitor", "trends", "env_score"]:
        with open(MOCK / f"{src}.csv", "rb") as f:
            r = client.post(f"/api/import/{src}", files={"file": (f"{src}.csv", f, "text/csv")})
            assert r.status_code == 200, r.text
    client.post("/api/calc/run")

    # 1. 缺货预警 ≥3 且含 SK-2087 紧急
    stockout = client.get("/api/alerts", params={"type": "缺货"}).json()["data"]
    assert len(stockout) >= 3, len(stockout)
    assert any(a["sku"] == "SK-2087" and a["level"] == "紧急" for a in stockout)
    print(f"  缺货预警 {len(stockout)} 条，含 SK-2087 紧急 OK")

    # 2. 滞销预警含 SK-0561/SK-8830
    slow = client.get("/api/alerts", params={"type": "滞销"}).json()["data"]
    skus = {a["sku"] for a in slow}
    assert "SK-0561" in skus and "SK-8830" in skus
    print("  滞销预警含 SK-0561/SK-8830 OK")

    # 3. 再跑一遍不重复创建
    before = len(client.get("/api/alerts").json()["data"])
    client.post("/api/calc/run")
    after = len(client.get("/api/alerts").json()["data"])
    assert before == after, f"{before} != {after}"
    print("  重复扫描不重复创建 OK")

    # 4. 阈值改小后预警数变多
    client.put("/api/settings/rules", json={"slow_mild_turnover": 30})
    client.post("/api/calc/run")
    increased = len(client.get("/api/alerts").json()["data"])
    assert increased > after, f"{increased} !> {after}"
    print("  阈值改 30 天后预警数变多 OK")

print("阶段 4 后端验收通过")
PYEOF
)

echo "[2/3] npm run build"
(cd "$FRONTEND" && npm run build >/dev/null)

echo "=== 阶段 4 验收通过 ==="
