"""测算触发路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ok
from app.engine.pipeline import run_calc

router = APIRouter()


@router.post("/calc/run")
def calc_run(db: Session = Depends(get_db)):
    """手动触发全量测算（定时任务同入口）。"""
    result = run_calc(db)
    return ok(result)
