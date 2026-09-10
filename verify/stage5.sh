#!/usr/bin/env bash
set -euo pipefail
# 阶段 5 验收门：生成分组草稿 / confirm-arrive 联动 / 预算 warning / 导出 / npm build

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PY="$ROOT/.venv/Scripts/python.exe"
[ -f "$PY" ] || PY="$ROOT/.venv/bin/python"

echo "=== 阶段 5 验收门 ==="

echo "[1/3] 重置数据库 + 导入 + 测算"
rm -f "$ROOT/data/stockwise.db"
(cd "$BACKEND" && "$PY" -m alembic upgrade head >/dev/null && "$PY" -m app.core.seed --mock >/dev/null)

(cd "$BACKEND" && "$PY" - <<'PYEOF'
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.db import SessionLocal
from app.models.inventory_snapshot import InventorySnapshot
from app.models.setting import Setting

MOCK = Path("../mock").resolve()
with TestClient(app) as client:
    for src in ["amazon_orders", "walmart_orders", "inventory_snapshot", "competitor", "trends", "env_score"]:
        with open(MOCK / f"{src}.csv", "rb") as f:
            r = client.post(f"/api/import/{src}", files={"file": (f"{src}.csv", f, "text/csv")})
            assert r.status_code == 200, r.text
    client.post("/api/calc/run")

    # 1. 3 SKU 生成 2 张按供应商分组草稿
    orders = client.post("/api/purchase-orders/generate", json={"skus": ["SK-1023", "SK-2087", "SK-4419"]}).json()["data"]
    assert len(orders) == 2
    assert {o["supplier"] for o in orders} == {"义乌XX宠物用品", "深圳XX家居"}
    print("  3 SKU 生成 2 张分组草稿 OK")

    # 2. confirm -> 在途增；arrive -> 在途减 + 库存增
    po = client.post("/api/purchase-orders/generate", json={"skus": ["SK-2087"]}).json()["data"][0]
    po_id, qty = po["id"], po["total_qty"]
    db = SessionLocal()
    b = db.query(InventorySnapshot).filter_by(sku="SK-2087").order_by(InventorySnapshot.date.desc()).first()
    t0, w0 = b.in_transit_qty, b.wfs_qty
    db.close()
    client.put(f"/api/purchase-orders/{po_id}/confirm")
    db = SessionLocal(); c = db.query(InventorySnapshot).filter_by(sku="SK-2087").order_by(InventorySnapshot.date.desc()).first(); db.close()
    assert c.in_transit_qty == t0 + qty
    client.put(f"/api/purchase-orders/{po_id}/ship")
    client.put(f"/api/purchase-orders/{po_id}/arrive")
    db = SessionLocal(); a = db.query(InventorySnapshot).filter_by(sku="SK-2087").order_by(InventorySnapshot.date.desc()).first(); db.close()
    assert a.in_transit_qty == t0 and a.wfs_qty == w0 + qty
    print("  confirm 在途增 / arrive 在途减 + 库存增 OK")

    # 3. 预算校验 warning
    db = SessionLocal()
    s = db.get(Setting, "monthly_budget"); s.value = 1; db.commit(); db.close()
    po2 = client.post("/api/purchase-orders/generate", json={"skus": ["SK-1023"]}).json()["data"][0]
    assert "budget" in po2["warning"]
    print("  预算校验 warning OK")

    # 4. 导出 xlsx 200
    r = client.get(f"/api/purchase-orders/{po2['id']}/export")
    assert r.status_code == 200 and "spreadsheetml" in r.headers.get("content-type", "")
    print("  导出 xlsx 200 OK")

print("阶段 5 后端验收通过")
PYEOF
)

echo "[2/3] npm run build"
(cd "$FRONTEND" && npm run build >/dev/null)

echo "=== 阶段 5 验收通过 ==="
