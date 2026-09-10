#!/usr/bin/env bash
set -euo pipefail
# E2E 全链路冒烟：seed -> 全量导入 -> calc -> 建议/预警/采购/看板/问答，生成验收报告.md

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PY="$ROOT/.venv/Scripts/python.exe"
[ -f "$PY" ] || PY="$ROOT/.venv/bin/python"

echo "=== E2E 全链路冒烟 ==="

echo "[1/3] pytest 全量"
(cd "$BACKEND" && "$PY" -m pytest -q)

echo "[2/3] 全新环境全链路"
rm -f "$ROOT/data/stockwise.db"
(cd "$BACKEND" && "$PY" -m alembic upgrade head >/dev/null && "$PY" -m app.core.seed --mock >/dev/null)

(cd "$BACKEND" && "$PY" - <<'PYEOF'
import time
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

MOCK = Path("../mock").resolve()
REPORT = Path("../验收报告.md").resolve()
results = []


def _check(cond, msg=""):
    if not cond:
        raise AssertionError(msg or "断言失败")
    return "ok"


def step(name, fn):
    t0 = time.perf_counter()
    passed, detail = True, ""
    try:
        detail = fn()
    except AssertionError as e:
        passed, detail = False, str(e)
    except Exception as e:
        passed, detail = False, repr(e)
    dur = (time.perf_counter() - t0) * 1000
    results.append((name, dur, passed, detail))


with TestClient(app) as client:
    step("GET /api/health", lambda: _check(client.get("/api/health").status_code == 200))
    for src in ["amazon_orders", "walmart_orders", "inventory_snapshot", "competitor", "trends", "env_score"]:
        def _import(src=src):
            with open(MOCK / f"{src}.csv", "rb") as f:
                r = client.post(f"/api/import/{src}", files={"file": (f"{src}.csv", f, "text/csv")})
            return _check(r.status_code == 200, f"status={r.status_code}")
        step(f"POST /api/import/{src}", _import)

    step("GET /api/datasources (6 源)", lambda: _check(len(client.get("/api/datasources").json()["data"]) == 6))

    def _calc():
        r = client.post("/api/calc/run")
        return _check(r.status_code == 200 and r.json()["data"]["count"] == 8, r.text[:80])
    step("POST /api/calc/run", _calc)

    step("GET /api/suggestions (8 行)", lambda: _check(len(client.get("/api/suggestions").json()["data"]) == 8))
    step("GET /api/alerts (≥6 条)", lambda: _check(len(client.get("/api/alerts").json()["data"]) >= 6))

    def _gen():
        r = client.post("/api/purchase-orders/generate", json={"skus": ["SK-1023", "SK-2087"]})
        return _check(r.status_code == 200 and len(r.json()["data"]) == 2)
    step("POST /api/purchase-orders/generate", _gen)

    step("GET /api/dashboard/summary", lambda: _check("kpi" in client.get("/api/dashboard/summary").json()["data"]))

    def _chat():
        d = client.post("/api/chat", json={"text": "本周要补什么货？"}).json()["data"]
        return _check("SK-" in d["answer_md"])
    step("POST /api/chat", _chat)

passed = sum(1 for _, _, p, _ in results if p)
lines = [
    "# 验收报告",
    "",
    f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    f"- 通过：{passed} / {len(results)} 项",
    "",
    "## 接口耗时与断言结果",
    "",
    "| 接口 | 耗时(ms) | 结果 | 备注 |",
    "|---|---|---|---|",
]
for name, dur, p, detail in results:
    lines.append(f"| {name} | {dur:.1f} | {'✅ 通过' if p else '❌ 失败'} | {detail} |")
lines += ["", "## 结论", ""]
lines.append("全链路冒烟通过。" if passed == len(results) else "存在失败项，需人工介入。")
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"验收报告已生成：{REPORT}")
print(f"结果：{passed}/{len(results)} 通过")
assert passed == len(results), "E2E 存在失败项"
PYEOF
)

echo "[3/3] npm run build"
(cd "$FRONTEND" && npm run build >/dev/null)

echo "=== E2E 全链路通过 ==="
