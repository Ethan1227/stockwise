"""采购计划路由。"""
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ok
from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase import GenerateRequest
from app.services import purchase

router = APIRouter()


@router.post("/purchase-orders/generate")
def generate(body: GenerateRequest, db: Session = Depends(get_db)):
    try:
        return ok(purchase.generate_purchase_orders(db, body.skus))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/purchase-orders")
def list_orders(status: str | None = Query(None), supplier: str | None = Query(None), db: Session = Depends(get_db)):
    q = db.query(PurchaseOrder)
    if status:
        q = q.filter(PurchaseOrder.status == status)
    if supplier:
        q = q.filter(PurchaseOrder.supplier == supplier)
    orders = q.order_by(PurchaseOrder.id.desc()).all()
    return ok([purchase.serialize(po) for po in orders])


@router.put("/purchase-orders/{po_id}/confirm")
def confirm(po_id: int, db: Session = Depends(get_db)):
    try:
        return ok(purchase.confirm_order(db, po_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/purchase-orders/{po_id}/ship")
def ship(po_id: int, db: Session = Depends(get_db)):
    try:
        return ok(purchase.ship_order(db, po_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/purchase-orders/{po_id}/arrive")
def arrive(po_id: int, db: Session = Depends(get_db)):
    try:
        return ok(purchase.arrive_order(db, po_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/purchase-orders/{po_id}")
def delete(po_id: int, db: Session = Depends(get_db)):
    try:
        return ok(purchase.delete_order(db, po_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/purchase-orders/{po_id}/export")
def export(po_id: int, db: Session = Depends(get_db)):
    po = db.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(status_code=404, detail="采购单不存在")
    wb = Workbook()
    ws = wb.active
    ws.title = po.po_no
    ws.append(["SKU", "品名", "数量", "单价", "金额"])
    for it in po.items_json.get("items", []):
        ws.append([it["sku"], it.get("name", ""), it["qty"], it["unit_cost"], it["amount"]])
    ws.append([])
    ws.append(["供应商", po.supplier])
    ws.append(["状态", po.status])
    ws.append(["总数量", po.total_qty])
    ws.append(["总金额", po.total_amount])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={po.po_no}.xlsx"},
    )
