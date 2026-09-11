"""评测指标路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.core.db import get_db
from app.core.exceptions import ok
from app.eval.ragas import evaluate_ragas
from app.eval.runner import run_all

router = APIRouter()


@router.get("/eval/metrics")
def eval_metrics(db: Session = Depends(get_db)):
    """返回各功能评测指标（准确率/精确率/召回率/F1）。"""
    return ok(run_all(db))


@router.get("/eval/ragas")
def eval_ragas(db: Session = Depends(get_db)):
    """返回 RAGAS 四指标（faithfulness/answer relevancy/context precision/context recall）。"""
    return ok(evaluate_ragas(db))


@router.get("/eval/docs")
def eval_docs():
    """返回测试说明文档 markdown。"""
    path = PROJECT_ROOT / "docs" / "06_测试说明.md"
    content = path.read_text(encoding="utf-8") if path.exists() else "# 测试说明文档\n\n（文档未找到）"
    return ok({"markdown": content})
