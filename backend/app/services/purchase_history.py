"""历史采购单导入（回填）：CSV -> purchase_order + 在途回写。

历史采购单不属于「数据中心」的 6 个数据源，是历史数据回填，故作为独立 service 而非数据源适配器。
"""
import csv
from datetime import date

from app.models.inventory_snapshot import InventorySnapshot
from app.models.purchase_order import PurchaseOrder


def _bump_transit(db, sku: str, qty: int):
    """shipped/confirmed 采购单计入对应 SKU 在途。"""
    inv = db.query(InventorySnapshot).filter_by(sku=sku).order_by(InventorySnapshot.date.desc()).first()
    if inv is not None:
        inv.in_transit_qty = inv.in_transit_qty + qty


def import_purchase_history(db, path: str) -> int:
    """读取历史采购单 CSV，按 po_no 分组入库；shipped/confirmed 计入在途。返回入库单数。"""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("po_no") or "").strip()]

    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["po_no"].strip(), []).append(r)

    for po_no, items in groups.items():
        first = items[0]
        po = db.query(PurchaseOrder).filter_by(po_no=po_no).first()
        if po is None:
            po = PurchaseOrder(po_no=po_no)
            db.add(po)
        po.supplier = (first.get("supplier") or "").strip()
        po.status = (first.get("status") or "draft").strip()
        po.dest_warehouse = (first.get("dest_warehouse") or "").strip()
        po.required_date = date.fromisoformat((first.get("required_date") or "").strip())
        po.items_json = {"items": [
            {
                "sku": (i.get("sku") or "").strip(),
                "qty": int(float(i.get("qty") or 0)),
                "unit_cost": float(i.get("unit_cost") or 0),
                "amount": float(i.get("amount") or 0),
            }
            for i in items
        ]}
        po.total_qty = sum(int(float(i.get("qty") or 0)) for i in items)
        po.total_amount = round(sum(float(i.get("amount") or 0) for i in items), 2)
        if po.status in ("confirmed", "shipped"):
            for i in items:
                _bump_transit(db, (i.get("sku") or "").strip(), int(float(i.get("qty") or 0)))

    return len(groups)
