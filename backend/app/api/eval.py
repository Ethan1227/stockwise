"""评测指标路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ok
from app.eval.runner import run_all

router = APIRouter()


@router.get("/eval/metrics")
def eval_metrics(db: Session = Depends(get_db)):
    """返回各功能评测指标（准确率/精确率/召回率/F1）。"""
    return ok(run_all(db))
