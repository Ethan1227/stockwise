#!/usr/bin/env bash
set -euo pipefail
# 阶段 3 验收门：建议列表 / 人工调整 / 导出 xlsx / npm build

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PY="$ROOT/.venv/Scripts/python.exe"
[ -f "$PY" ] || PY="$ROOT/.venv/bin/python"

echo "=== 阶段 3 验收门 ==="

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
    assert client.post("/api/calc/run").status_code == 200

    # 1. 列表按评分降序 + 字段齐全
    data = client.get("/api/suggestions").json()["data"]
    scores = [d["score"] for d in data]
    assert scores == sorted(scores, reverse=True), "评分未降序"
    for k in ["sku", "platform", "forecast_daily", "sellable_days", "suggest_qty", "score", "reason_text"]:
        assert k in data[0], f"缺字段 {k}"
    print(f"  建议列表 {len(data)} 行，评分降序 + 字段齐全 OK")

    # 2. 人工改量
    client.put("/api/suggestions/SK-1023", json={"adjusted_qty": 500, "note": "人工加量"})
    row = next(d for d in client.get("/api/suggestions").json()["data"] if d["sku"] == "SK-1023")
    assert row["is_adjusted"] is True and row["effective_qty"] == 500
    print("  PUT 改量后 GET 显示人工值且标已调整 OK")

    # 3. 导出 xlsx
    r = client.get("/api/suggestions/export")
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers.get("content-type", "")
    print("  导出 xlsx Content-Type 正确 OK")

print("阶段 3 后端验收通过")
PYEOF
)

echo "[2/3] npm run build"
(cd "$FRONTEND" && npm run build >/dev/null)

echo "=== 阶段 3 验收通过 ==="
