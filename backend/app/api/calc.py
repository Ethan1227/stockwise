"""测算触发与历史回测路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ok
from app.engine.pipeline import run_calc
from app.models.calc_result import CalcResult
from app.services.alert import scan_alerts

router = APIRouter()


@router.post("/calc/run")
def calc_run(db: Session = Depends(get_db)):
    """手动触发全量测算 + 预警扫描（定时任务同入口）。"""
    result = run_calc(db)
    result["alerts_created"] = scan_alerts(db)
    return ok(result)


@router.get("/calc/history")
def calc_history(db: Session = Depends(get_db)):
    """测算历史：各测算日期的 SKU 数量。"""
    dates = db.query(CalcResult.calc_date).distinct().order_by(CalcResult.calc_date.desc()).all()
    data = [
        {
            "calc_date": d.isoformat(),
            "count": db.query(func.count(CalcResult.id)).filter(CalcResult.calc_date == d).scalar(),
        }
        for (d,) in dates
    ]
    return ok(data)


@router.get("/calc/history/{sku}")
def sku_history(sku: str, db: Session = Depends(get_db)):
    """单 SKU 测算历史趋势（评分/预测日销/建议量随日期变化）。"""
    rows = db.query(CalcResult).filter(CalcResult.sku == sku).order_by(CalcResult.calc_date).all()
    return ok([
        {
            "calc_date": r.calc_date.isoformat(),
            "forecast_daily": r.forecast_daily,
            "score": r.score,
            "score_band": r.score_band,
            "suggest_qty": r.suggest_qty,
            "sellable_days": r.sellable_days,
        }
        for r in rows
    ])
