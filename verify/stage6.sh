#!/usr/bin/env bash
set -euo pipefail
# 阶段 6 验收门：summary 预警数与 S4 一致 / 待办含黑五倒计时 / npm build

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PY="$ROOT/.venv/Scripts/python.exe"
[ -f "$PY" ] || PY="$ROOT/.venv/bin/python"

echo "=== 阶段 6 验收门 ==="

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

    summary = client.get("/api/dashboard/summary").json()["data"]
    # 1. 预警数与 S4 接口实际数一致
    stockout_actual = len(client.get("/api/alerts", params={"type": "缺货"}).json()["data"])
    slow_actual = len(client.get("/api/alerts", params={"type": "滞销"}).json()["data"])
    assert summary["kpi"]["stockout"] == stockout_actual, (summary["kpi"]["stockout"], stockout_actual)
    assert summary["kpi"]["slow"] == slow_actual
    print(f"  summary 预警数（缺货{stockout_actual}/滞销{slow_actual}）与 S4 一致 OK")

    # 2. 待办含黑五倒计时
    big = [t for t in summary["todos"] if t["type"] == "大促"]
    assert big and "倒计时" in big[0]["text"]
    print("  待办含黑五倒计时 OK")

print("阶段 6 后端验收通过")
PYEOF
)

echo "[2/3] npm run build"
(cd "$FRONTEND" && npm run build >/dev/null)

echo "=== 阶段 6 验收通过 ==="
