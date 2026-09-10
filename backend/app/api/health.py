"""健康检查路由。"""
from fastapi import APIRouter

from app.core.exceptions import ok

router = APIRouter()


@router.get("/health")
def health():
    """GET /api/health：服务健康检查。"""
    return ok({"status": "ok", "version": "1.0.0"})
