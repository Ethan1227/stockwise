"""测算流水线：基线日销 -> 修正器链 -> 预测日销 -> 评分 -> 建议备货量 -> calc_result。"""
import math
from datetime import date, timedelta

from app.engine.modifiers import ALL_MODIFIER_CODES, registry
from app.engine.scoring import compute_score, score_band
from app.models.calc_result import CalcResult
from app.models.daily_sales import DailySales
from app.models.inventory_snapshot import InventorySnapshot
from app.models.sku_master import SkuMaster


def _avg_qty(db, sku, start: date, end: date):
    """剔除断货日后的日均销量；无数据返回 None。"""
    rows = (
        db.query(DailySales)
        .filter(
            DailySales.sku == sku.sku,
            DailySales.date >= start,
            DailySales.date < end,
            DailySales.is_stockout_day.is_(False),
        )
        .all()
    )
    if not rows:
        return None
    return sum(r.qty for r in rows) / len(rows)


def compute_base_daily(db, sku, settings: dict, today: date) -> float:
    """基线日销 = 近30天×0.5 + 近90天×0.3 + 去年同期×0.2；缺去年数据转 0.6/0.4。"""
    w = settings["base_weights"]
    d30 = _avg_qty(db, sku, today - timedelta(days=30), today) or 0.0
    d90 = _avg_qty(db, sku, today - timedelta(days=90), today) or 0.0
    # 去年同期 = 去年整年可用数据（mock 中即 2025 黑五窗口）
    yoy = _avg_qty(db, sku, date(today.year - 1, 1, 1), date(today.year, 1, 1))
    if yoy is not None:
        return d30 * w["30d"] + d90 * w["90d"] + yoy * w["yoy"]
    return d30 * 0.6 + d90 * 0.4


def compute_sellable(sku, inventory) -> int:
    """可售库存：按平台取对应仓库存。"""
    if inventory is None:
        return 0
    if sku.platform == "亚马逊":
        return inventory.fba_qty
    if sku.platform == "沃尔玛":
        return inventory.wfs_qty
    return inventory.fba_qty + inventory.wfs_qty  # 双平台


def compute_suggest_qty(sku, forecast: float, inventory, lead_shelf_days: int) -> int:
    """建议备货量 = 预测日销×备货周期 − 可售 − 在途，负取 0，按 MOQ 向上取整。"""
    sellable = compute_sellable(sku, inventory)
    in_transit = inventory.in_transit_qty if inventory else 0
    lead_cycle = sku.lead_prod_days + sku.lead_ship_days + lead_shelf_days + sku.safety_days
    qty = max(0.0, forecast * lead_cycle - sellable - in_transit)
    moq = sku.moq or 1
    return math.ceil(qty / moq) * moq


def calc_one(db, sku: SkuMaster, settings: dict, today: date) -> CalcResult:
    base_daily = compute_base_daily(db, sku, settings, today)
    ctx = {"db": db, "settings": settings, "calc_date": today, "base_daily": base_daily}

    factors: dict = {}
    reasons: list[str] = []
    missing_signals: list[str] = []
    for code in ALL_MODIFIER_CODES:
        mod = registry.get(code)
        if mod is None:  # 已注销 -> 按 1.0 降级
            factors[code] = 1.0
            reasons.append(f"{code} 信号缺失（已注销）")
            missing_signals.append(code)
            continue
        try:
            coeff, reason = mod.factor(sku, ctx)
        except Exception:
            coeff, reason = 1.0, f"{mod.name}信号缺失"
        factors[code] = coeff
        if reason:
            reasons.append(reason)
        if "缺失" in reason:
            missing_signals.append(code)

    forecast = base_daily
    for c in factors.values():
        forecast *= c

    inventory = (
        db.query(InventorySnapshot)
        .filter_by(sku=sku.sku)
        .order_by(InventorySnapshot.date.desc())
        .first()
    )
    sellable = compute_sellable(sku, inventory)
    sellable_days = sellable / forecast if forecast > 0 else 999.0

    lead_shelf_days = settings.get("lead_shelf_days", 5)
    score, detail = compute_score(sku, forecast, factors, sellable_days, lead_shelf_days)
    suggest_qty = compute_suggest_qty(sku, forecast, inventory, lead_shelf_days)

    obj = db.query(CalcResult).filter_by(sku=sku.sku, calc_date=today).first()
    if obj is None:
        obj = CalcResult(sku=sku.sku, calc_date=today)
        db.add(obj)
    obj.base_daily = round(base_daily, 2)
    obj.forecast_daily = round(forecast, 2)
    obj.score = score
    obj.score_band = score_band(score)
    obj.suggest_qty = suggest_qty
    obj.sellable_days = round(sellable_days, 2)
    obj.factors_json = factors
    obj.score_detail_json = detail
    obj.reason_text = "；".join(reasons)
    obj.data_flags = {"missing_signals": missing_signals}
    return obj


def run_calc(db) -> dict:
    from app.services.settings import load_settings

    settings = load_settings(db)
    today = date.today()
    skus = db.query(SkuMaster).all()
    for sku in skus:
        calc_one(db, sku, settings, today)
    db.commit()
    return {"calc_date": today.isoformat(), "count": len(skus)}
