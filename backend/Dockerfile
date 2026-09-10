FROM python:3.12-slim

WORKDIR /app

# 先装依赖（利用 Docker 缓存层）
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 拷贝源码与 mock 数据（config 按 __file__ 定位 /app/mock、/app/data）
COPY backend/ ./backend/
COPY mock/ ./mock/

WORKDIR /app/backend
EXPOSE 8000

# 默认命令：迁移 + API 服务（1 worker，调度由独立 scheduler 服务承载）
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
