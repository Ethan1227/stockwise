"""FastAPI 入口：只挂 router，统一异常与响应格式。"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models  # noqa: F401  # 注册全部模型
from app.api import alerts, calc, chat, dashboard, health, imports, purchase_orders, settings, skus, suggestions
from app.api import eval as eval_api
from app.core.db import Base, engine
from app.core.exceptions import BusinessError
from app.core.feature_flags import check_feature


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 首次启动自动建表（调度已拆分为独立进程 app.scheduler_worker）
    Base.metadata.create_all(bind=engine)
    yield


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


app.include_router(health.router, prefix="/api")  # 健康检查不设开关
app.include_router(imports.router, prefix="/api", dependencies=[Depends(check_feature("datacenter"))])
app.include_router(calc.router, prefix="/api", dependencies=[Depends(check_feature("engine"))])
app.include_router(suggestions.router, prefix="/api", dependencies=[Depends(check_feature("suggestion"))])
app.include_router(alerts.router, prefix="/api", dependencies=[Depends(check_feature("alert"))])
app.include_router(purchase_orders.router, prefix="/api", dependencies=[Depends(check_feature("purchase"))])
app.include_router(dashboard.router, prefix="/api", dependencies=[Depends(check_feature("dashboard"))])
app.include_router(chat.router, prefix="/api", dependencies=[Depends(check_feature("chat"))])
app.include_router(skus.router, prefix="/api", dependencies=[Depends(check_feature("settings"))])
app.include_router(settings.router, prefix="/api", dependencies=[Depends(check_feature("settings"))])
app.include_router(eval_api.router, prefix="/api")  # 评测指标不设开关
