"""测算引擎测试：手工验算对拍 + 修正器注销降级。"""
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, engine
from app.core.seed import seed_default_settings, seed_promotion_calendar, seed_sku_master
from app.datasources import registry
from app.engine import modifiers as modifiers_pkg
from app.engine.modifiers import registry as mod_registry
from app.engine.pipeline import compute_base_daily, run_calc
from app.models.calc_result import CalcResult
from app.models.daily_sales import DailySales
from app.models.sku_master import SkuMaster

MOCK = Path(__file__).resolve().parents[2] / "mock"


def _load_all(db: Session):
    seed_sku_master(db)
    seed_default_settings(db)
    seed_promotion_calendar(db, use_csv=True)
    for src in ["amazon_orders", "walmart_orders", "inventory_snapshot", "competitor", "trends", "env_score"]:
        registry.run(src, db, str(MOCK / f"{src}.csv"))
    db.commit()


@pytest.fixture(scope="module")
def db() -> Session:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    _load_all(session)
    yield session
    session.close()


def _recompute_base(db, sku_code: str, today: date) -> float:
    """独立重算基线（对拍基准）。"""
    sku = db.query(SkuMaster).filter_by(sku=sku_code).first()
    d30 = _avg(db, sku, today - timedelta(days=30), today)
    d90 = _avg(db, sku, today - timedelta(days=90), today)
    yoy = _avg(db, sku, date(today.year - 1, 1, 1), date(today.year, 1, 1))
    if yoy is not None:
        return d30 * 0.5 + d90 * 0.3 + yoy * 0.2
    return d30 * 0.6 + d90 * 0.4


def _avg(db, sku, start, end):
    rows = (
        db.query(DailySales)
        .filter(DailySales.sku == sku.sku, DailySales.date >= start, DailySales.date < end, DailySales.is_stockout_day.is_(False))
        .all()
    )
    return (sum(r.qty for r in rows) / len(rows)) if rows else None


def test_calc_result_count(db):
    run_calc(db)
    assert db.query(CalcResult).count() == db.query(SkuMaster).count() == 8


def test_sk2087_base_and_forecast(db):
    today = date.today()
    expected_base = _recompute_base(db, "SK-2087", today)
    result = db.query(CalcResult).filter_by(sku="SK-2087", calc_date=today).first()
    assert result is not None
    assert result.base_daily == pytest.approx(expected_base, abs=0.5)
    assert 8.7 <= result.forecast_daily <= 10.7
    assert result.reason_text


def test_sk1023_high_score(db):
    today = date.today()
    result = db.query(CalcResult).filter_by(sku="SK-1023", calc_date=today).first()
    assert result.score >= 80
    assert result.factors_json["trend"] == 1.2


def test_unregister_trend_degrades_to_1(db):
    mod_registry.unregister("trend")
    try:
        run_calc(db)
        today = date.today()
        result = db.query(CalcResult).filter_by(sku="SK-1023", calc_date=today).first()
        assert result.factors_json["trend"] == 1.0
        assert "信号缺失" in result.reason_text
    finally:
        # 恢复注册
        import importlib
        importlib.reload(modifiers_pkg)
