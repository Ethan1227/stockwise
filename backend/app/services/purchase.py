"""采购计划编排：建议 -> 采购单，预算校验、交期倒排、状态机、到货回写。"""
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.calc_result import CalcResult
from app.models.inventory_snapshot import InventorySnapshot
from app.models.purchase_order import PurchaseOrder
from app.models.sku_master import SkuMaster
from app.models.suggestion_override import SuggestionOverride
from app.services.settings import load_settings
from app.services.suggestion import latest_calc_date


def dest_warehouse(platform: str) -> str:
    if platform == "亚马逊":
        return "FBA"
    if platform == "沃尔玛":
        return "WFS"
    return "FBA+WFS"


def serialize(po: PurchaseOrder) -> dict:
    return {
        "id": po.id,
        "po_no": po.po_no,
        "supplier": po.supplier,
        "status": po.status,
        "total_qty": po.total_qty,
        "total_amount": po.total_amount,
        "dest_warehouse": po.dest_warehouse,
        "items": po.items_json.get("items", []),
        "suggest_air": po.suggest_air,
        "warning": po.warning,
        "created_at": po.created_at.isoformat() if po.created_at else None,
    }


def _lead_time_check(settings: dict, today: date) -> tuple[bool, str]:
    """交期倒排：未来最近大促，入仓截止日距今天 < 头程+上架 则建议空运。"""
    upcoming = []
    for ev in settings.get("promotion_calendar", []):
        try:
            d = date.fromisoformat(ev["event_date"])
            deadline = date.fromisoformat(ev["warehouse_deadline"])
        except (KeyError, ValueError):
            continue
        if d >= today:
            upcoming.append((d, deadline))
    if not upcoming:
        return False, ""
    _, nearest_deadline = min(upcoming, key=lambda x: x[0])
    sea = settings["lead_transit_sea"]
    shelf = settings["lead_shelf_days"]
    if (nearest_deadline - today).days < sea + shelf:
        return True, f"海运来不及（入仓截止 {nearest_deadline}），建议改空运"
    return False, ""


def generate_purchase_orders(db: Session, sku_codes: list[str]) -> list[dict]:
    settings = load_settings(db)
    calc_date = latest_calc_date(db)
    today = date.today()
    budget = settings["monthly_budget"]

    groups: dict[tuple[str, str], list[dict]] = {}
    for code in sku_codes:
        sku = db.query(SkuMaster).filter_by(sku=code).first()
        if sku is None:
            continue
        cr = db.query(CalcResult).filter_by(sku=code, calc_date=calc_date).first()
        if cr is None:
            continue
        ov = db.query(SuggestionOverride).filter_by(sku=code, calc_date=calc_date).first()
        qty = ov.adjusted_qty if (ov and ov.adjusted_qty is not None) else cr.suggest_qty
        if qty <= 0:
            continue
        groups.setdefault((sku.supplier, dest_warehouse(sku.platform)), []).append(
            {"sku": code, "name": sku.name, "qty": qty, "unit_cost": sku.unit_cost, "amount": round(qty * sku.unit_cost, 2)}
        )

    today_po_count = (
        db.query(func.count(PurchaseOrder.id))
        .filter(PurchaseOrder.po_no.like(f"PO-{today:%Y%m%d}-%"))
        .scalar()
        or 0
    )
    seq = today_po_count + 1
    orders = []
    total_amount = 0.0
    for (supplier, dw), items in groups.items():
        po = PurchaseOrder(
            po_no=f"PO-{today:%Y%m%d}-{seq:02d}",
            supplier=supplier,
            status="draft",
            total_qty=sum(i["qty"] for i in items),
            total_amount=round(sum(i["amount"] for i in items), 2),
            dest_warehouse=dw,
            items_json={"items": items},
            suggest_air=False,
            warning={},
        )
        db.add(po)
        orders.append(po)
        total_amount += po.total_amount
        seq += 1

    db.flush()

    air, msg = _lead_time_check(settings, today)
    for po in orders:
        warning = dict(po.warning or {})
        if total_amount > budget:
            warning["budget"] = f"合计金额 {total_amount} 超月预算 {budget}"
        if air:
            po.suggest_air = True
            warning["lead_time"] = msg
        po.warning = warning

    db.commit()
    return [serialize(po) for po in orders]


def _bump_inventory(db: Session, sku_code: str, delta_transit: int = 0, delta_fba: int = 0, delta_wfs: int = 0):
    inv = db.query(InventorySnapshot).filter_by(sku=sku_code).order_by(InventorySnapshot.date.desc()).first()
    if inv is None:
        return
    inv.in_transit_qty = max(0, inv.in_transit_qty + delta_transit)
    inv.fba_qty = max(0, inv.fba_qty + delta_fba)
    inv.wfs_qty = max(0, inv.wfs_qty + delta_wfs)


def _get_po(db: Session, po_id: int) -> PurchaseOrder:
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise ValueError("采购单不存在")
    return po


def confirm_order(db: Session, po_id: int) -> dict:
    po = _get_po(db, po_id)
    if po.status != "draft":
        raise ValueError(f"仅草稿可确认，当前 {po.status}")
    po.status = "confirmed"
    for it in po.items_json.get("items", []):
        _bump_inventory(db, it["sku"], delta_transit=it["qty"])
    db.commit()
    return serialize(po)


def ship_order(db: Session, po_id: int) -> dict:
    po = _get_po(db, po_id)
    if po.status != "confirmed":
        raise ValueError(f"仅已确认可发货，当前 {po.status}")
    po.status = "shipped"
    db.commit()
    return serialize(po)


def arrive_order(db: Session, po_id: int) -> dict:
    po = _get_po(db, po_id)
    if po.status != "shipped":
        raise ValueError(f"仅已发货可到货，当前 {po.status}")
    po.status = "arrived"
    is_fba = "FBA" in po.dest_warehouse
    is_wfs = "WFS" in po.dest_warehouse
    for it in po.items_json.get("items", []):
        _bump_inventory(
            db,
            it["sku"],
            delta_transit=-it["qty"],
            delta_fba=it["qty"] if is_fba else 0,
            delta_wfs=it["qty"] if is_wfs else 0,
        )
    db.commit()
    return serialize(po)


def delete_order(db: Session, po_id: int) -> dict:
    po = _get_po(db, po_id)
    if po.status != "draft":
        raise ValueError("仅草稿可删除")
    db.delete(po)
    db.commit()
    return {"id": po_id, "deleted": True}
