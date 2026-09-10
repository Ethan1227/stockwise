FROM python:3.12-slim

WORKDIR /app

# PyPI 镜像（国内网络可用清华源；海外可 --build-arg PIP_INDEX_URL=https://pypi.org/simple）
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 先装依赖（利用 Docker 缓存层）
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -i ${PIP_INDEX_URL}

# 拷贝源码与 mock 数据（config 按 __file__ 定位 /app/mock、/app/data）
COPY backend/ ./backend/
COPY mock/ ./mock/

WORKDIR /app/backend
# 让 alembic 控制台脚本能 import app（console script 不会自动把 CWD 加入 sys.path）
ENV PYTHONPATH=/app/backend
EXPOSE 8000

# 默认命令：迁移 + API 服务（1 worker，调度由独立 scheduler 服务承载）
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
