#!/usr/bin/env bash
set -euo pipefail
# 阶段 2 验收门：pytest 对拍 / calc_result 行数 / SK-2087 forecast 区间 / 注销降级

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
PY="$ROOT/.venv/Scripts/python.exe"
[ -f "$PY" ] || PY="$ROOT/.venv/bin/python"

echo "=== 阶段 2 验收门 ==="

echo "[1/3] pytest tests/test_engine.py"
(cd "$BACKEND" && "$PY" -m pytest tests/test_engine.py -q)

echo "[2/3] 重置数据库 + 迁移 + seed"
rm -f "$ROOT/data/stockwise.db"
(cd "$BACKEND" && "$PY" -m alembic upgrade head >/dev/null && "$PY" -m app.core.seed --mock >/dev/null)

echo "[3/3] calc/run 断言"
(cd "$BACKEND" && "$PY" - <<'PYEOF'
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.datasources import registry
from app.engine.modifiers import registry as mod_registry
from app.engine.pipeline import run_calc
from app.main import app
from app.models.calc_result import CalcResult

MOCK = Path("../mock").resolve()

with TestClient(app) as client:
    for src in ["amazon_orders", "walmart_orders", "inventory_snapshot", "competitor", "trends", "env_score"]:
        with open(MOCK / f"{src}.csv", "rb") as f:
            r = client.post(f"/api/import/{src}", files={"file": (f"{src}.csv", f, "text/csv")})
            assert r.status_code == 200, (src, r.text)

    r = client.post("/api/calc/run")
    assert r.status_code == 200, r.text
    assert r.json()["data"]["count"] == 8
    print("  calc/run 行数 = 8 OK")

db = SessionLocal()
try:
    res = db.query(CalcResult).filter_by(sku="SK-2087", calc_date=date.today()).first()
    assert res is not None
    assert 8.7 <= res.forecast_daily <= 10.7, res.forecast_daily
    assert res.reason_text
    print(f"  SK-2087 forecast={res.forecast_daily} in [8.7,10.7] OK")

    mod_registry.unregister("trend")
    run_calc(db)
    res2 = db.query(CalcResult).filter_by(sku="SK-1023", calc_date=date.today()).first()
    assert res2.factors_json["trend"] == 1.0
    print("  注销 trend_modifier -> 系数 1.0 OK")
finally:
    db.close()

print("阶段 2 验收通过")
PYEOF
)

echo "=== 阶段 2 验收通过 ==="
