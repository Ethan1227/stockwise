#!/usr/bin/env bash
set -euo pipefail
# 阶段 0 验收门：health / alembic / seed / npm build

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PY="$ROOT/.venv/Scripts/python.exe"
[ -f "$PY" ] || PY="$ROOT/.venv/bin/python"

echo "=== 阶段 0 验收门 ==="

echo "[1/4] alembic upgrade head"
(cd "$BACKEND" && "$PY" -m alembic upgrade head)

echo "[2/4] python -m app.core.seed --mock"
(cd "$BACKEND" && "$PY" -m app.core.seed --mock)

echo "[3/4] GET /api/health 返回 200"
(cd "$BACKEND" && "$PY" -c "
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as c:
    r = c.get('/api/health')
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['code'] == 0 and body['data']['status'] == 'ok', body
    print('health ok:', body)
")

echo "[4/4] npm run build"
(cd "$FRONTEND" && npm run build)

echo "=== 阶段 0 验收通过 ==="
