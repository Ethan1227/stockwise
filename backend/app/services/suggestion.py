"""备货建议编排：只读 calc_result，人工改量写 suggestion_override。"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.calc_result import CalcResult
from app.models.inventory_snapshot import InventorySnapshot
from app.models.sku_master import SkuMaster
from app.models.suggestion_override import SuggestionOverride


def latest_calc_date(db: Session):
    return db.query(func.max(CalcResult.calc_date)).scalar()


def get_suggestions(db: Session, platform: str | None = None, score_band: str | None = None, status: str | None = None) -> list[dict]:
    """备货建议列表（最新测算期，按评分降序）。"""
    calc_date = latest_calc_date(db)
    if calc_date is None:
        return []

    query = (
        db.query(CalcResult, SkuMaster)
        .join(SkuMaster, SkuMaster.sku == CalcResult.sku)
        .filter(CalcResult.calc_date == calc_date)
    )
    if platform:
        query = query.filter(SkuMaster.platform == platform)
    if score_band:
        query = query.filter(CalcResult.score_band == score_band)

    items = []
    for cr, sku in query.all():
        inv = (
            db.query(InventorySnapshot)
            .filter_by(sku=sku.sku)
            .order_by(InventorySnapshot.date.desc())
            .first()
        )
        ov = db.query(SuggestionOverride).filter_by(sku=sku.sku, calc_date=calc_date).first()
        adjusted_qty = ov.adjusted_qty if ov else None
        is_ignored = ov is not None and ov.adjusted_qty is None
        is_adjusted = ov is not None and ov.adjusted_qty is not None

        item = {
            "sku": sku.sku,
            "name": sku.name,
            "platform": sku.platform,
            "category": sku.category,
            "supplier": sku.supplier,
            "fba_qty": inv.fba_qty if inv else 0,
            "wfs_qty": inv.wfs_qty if inv else 0,
            "cn_qty": inv.cn_qty if inv else 0,
            "in_transit_qty": inv.in_transit_qty if inv else 0,
            "forecast_daily": cr.forecast_daily,
            "sellable_days": cr.sellable_days,
            "suggest_qty": cr.suggest_qty,
            "score": cr.score,
            "score_band": cr.score_band,
            "score_detail": cr.score_detail_json,
            "reason_text": cr.reason_text,
            "data_flags": cr.data_flags,
            "adjusted_qty": adjusted_qty,
            "is_adjusted": is_adjusted,
            "is_ignored": is_ignored,
            "effective_qty": adjusted_qty if is_adjusted else cr.suggest_qty,
        }
        items.append(item)

    if status == "adjusted":
        items = [i for i in items if i["is_adjusted"]]
    elif status == "ignored":
        items = [i for i in items if i["is_ignored"]]

    items.sort(key=lambda x: -x["score"])
    return items


def update_override(db: Session, sku_code: str, adjusted_qty: int | None, note: str, operator: str = "system") -> dict:
    """写入/更新人工改量或忽略。"""
    calc_date = latest_calc_date(db)
    if calc_date is None:
        raise ValueError("尚无测算结果，请先执行测算")
    obj = db.query(SuggestionOverride).filter_by(sku=sku_code, calc_date=calc_date).first()
    if obj is None:
        obj = SuggestionOverride(sku=sku_code, calc_date=calc_date)
        db.add(obj)
    obj.adjusted_qty = adjusted_qty
    obj.adjusted_by = operator
    obj.note = note
    db.commit()
    return {"sku": sku_code, "calc_date": calc_date.isoformat(), "adjusted_qty": adjusted_qty, "note": note}
