#!/usr/bin/env bash
set -euo pipefail
# 阶段 1 验收门：6 源导入 / 幂等 / 缺列 400 / 数据源状态 / npm build

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PY="$ROOT/.venv/Scripts/python.exe"
[ -f "$PY" ] || PY="$ROOT/.venv/bin/python"

echo "=== 阶段 1 验收门 ==="

echo "[1/3] 重置数据库 + 迁移 + seed"
rm -f "$ROOT/data/stockwise.db"
(cd "$BACKEND" && "$PY" -m alembic upgrade head >/dev/null && "$PY" -m app.core.seed --mock >/dev/null)

echo "[2/3] 导入验收"
(cd "$BACKEND" && "$PY" - <<'PYEOF'
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

MOCK = Path("../mock").resolve()

def upload(client, source, name):
    with open(MOCK / name, "rb") as f:
        return client.post(f"/api/import/{source}", files={"file": (name, f, "text/csv")})

expected = {
    "amazon_orders": ("amazon_orders.csv", 696),
    "walmart_orders": ("walmart_orders.csv", 348),
    "inventory_snapshot": ("inventory_snapshot.csv", 8),
    "competitor": ("competitor.csv", 6),
    "trends": ("trends.csv", 8),
    "env_score": ("env_score.csv", 5),
}

with TestClient(app) as client:
    for source, (name, count) in expected.items():
        r = upload(client, source, name)
        assert r.status_code == 200, (source, r.text)
        written = r.json()["data"]["written"]
        assert written == count, f"{source} 写入 {written} != {count}"
        print(f"  {source}: 写入 {written} 行 OK")

    r1 = upload(client, "inventory_snapshot", "inventory_snapshot.csv")
    r2 = upload(client, "inventory_snapshot", "inventory_snapshot.csv")
    assert r1.json()["data"]["written"] == r2.json()["data"]["written"] == 8
    print("  重复导入 inventory_snapshot 幂等 OK")

    bad = "sku,date\nSK-1,2026-01-01\n".encode()
    r = client.post("/api/import/amazon_orders", files={"file": ("bad.csv", bad, "text/csv")})
    assert r.status_code == 400, r.text
    print("  缺列文件 400 OK")

    r = client.get("/api/datasources")
    assert len(r.json()["data"]) == 6
    print("  GET /api/datasources 6 源 OK")

print("导入验收通过")
PYEOF
)

echo "[3/3] npm run build"
(cd "$FRONTEND" && npm run build >/dev/null)

echo "=== 阶段 1 验收通过 ==="
