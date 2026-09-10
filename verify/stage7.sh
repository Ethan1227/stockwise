#!/usr/bin/env bash
set -euo pipefail
# 阶段 7 验收门：6 类问答断言 / generate_po 真出草稿 / 兜底 / npm build

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PY="$ROOT/.venv/Scripts/python.exe"
[ -f "$PY" ] || PY="$ROOT/.venv/bin/python"

echo "=== 阶段 7 验收门 ==="

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

    # 1. 补货清单含 Top SKU
    d = client.post("/api/chat", json={"text": "本周要补什么货？"}).json()["data"]
    assert "SK-" in d["answer_md"] and d["data_chips"]
    print("  补货清单含 Top SKU OK")

    # 2. 断货含 SK-2087 与 空运
    d = client.post("/api/chat", json={"text": "SK-2087 会断货吗？"}).json()["data"]
    assert "SK-2087" in d["answer_md"] and "空运" in d["answer_md"]
    print("  断货问题含 SK-2087 与 空运 OK")

    # 3. 滞销含 SK-0561
    d = client.post("/api/chat", json={"text": "哪些产品滞销？"}).json()["data"]
    assert "SK-0561" in d["answer_md"]
    print("  滞销问题含 SK-0561 OK")

    # 4. generate_po 真出草稿
    before = len(client.get("/api/purchase-orders").json()["data"])
    client.post("/api/chat", json={"text": "生成采购计划"})
    after = len(client.get("/api/purchase-orders").json()["data"])
    assert after > before
    print("  generate_po 后 M5 多出草稿 OK")

    # 5. 未命中返回兜底
    d = client.post("/api/chat", json={"text": "今天吃什么？"}).json()["data"]
    assert d["suggestions"]
    print("  未命中返回兜底 OK")

print("阶段 7 后端验收通过")
PYEOF
)

echo "[2/3] npm run build"
(cd "$FRONTEND" && npm run build >/dev/null)

echo "=== 阶段 7 验收通过 ==="
