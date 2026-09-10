"""备货建议路由。"""
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ok
from app.schemas.suggestion import SuggestionUpdate
from app.services.suggestion import get_suggestions, update_override

router = APIRouter()


@router.get("/suggestions")
def list_suggestions(
    platform: str | None = Query(None),
    score_band: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return ok(get_suggestions(db, platform, score_band, status))


@router.put("/suggestions/{sku}")
def put_suggestion(sku: str, body: SuggestionUpdate, db: Session = Depends(get_db)):
    try:
        return ok(update_override(db, sku, body.adjusted_qty, body.note))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/suggestions/export")
def export_suggestions(db: Session = Depends(get_db)):
    items = get_suggestions(db)
    wb = Workbook()
    ws = wb.active
    ws.title = "备货建议"
    headers = ["SKU", "品名", "平台", "类目", "供应商", "预测日销", "可售天数", "建议备货量", "评分", "分档", "评分依据", "测算依据"]
    ws.append(headers)
    for it in items:
        ws.append([
            it["sku"], it["name"], it["platform"], it["category"], it["supplier"],
            it["forecast_daily"], it["sellable_days"], it["effective_qty"], it["score"],
            it["score_band"], str(it["score_detail"]), it["reason_text"],
        ])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=suggestions.xlsx"},
    )
