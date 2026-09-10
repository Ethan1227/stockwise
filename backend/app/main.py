"""FastAPI 入口：只挂 router，统一异常与响应格式。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models  # noqa: F401  # 注册全部模型
from app.api import calc, health, imports
from app.core.db import Base, engine
from app.core.exceptions import BusinessError
from app.core.scheduler import scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 首次启动自动建表
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="智备货 StockWise", version="1.0.0", lifespan=lifespan)

# 开发期跨域：前端代理 /api -> 8000，仍放开以便直接调试
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BusinessError)
async def business_error_handler(request, exc: BusinessError):
    """业务异常统一转为 {code, data, message}。"""
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "data": None, "message": exc.message},
    )


app.include_router(health.router, prefix="/api")
app.include_router(imports.router, prefix="/api")
app.include_router(calc.router, prefix="/api")
