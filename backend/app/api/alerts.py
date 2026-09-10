"""预警中心与规则配置路由。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import BusinessError, ok
from app.models.alert import Alert
from app.models.setting import Setting
from app.services.settings import load_settings

router = APIRouter()


def _serialize(a: Alert) -> dict:
    return {
        "id": a.id,
        "sku": a.sku,
        "code": a.code,
        "alert_type": a.alert_type,
        "level": a.level,
        "title": a.title,
        "detail": a.detail,
        "advice": a.advice,
        "status": a.status,
        "notify_log": a.notify_log,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.get("/alerts")
def list_alerts(
    type: str | None = Query(None),
    level: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Alert)
    if type:
        q = q.filter(Alert.alert_type == type)
    if level:
        q = q.filter(Alert.level == level)
    if status:
        q = q.filter(Alert.status == status)
    alerts = q.order_by(Alert.created_at.desc()).all()
    return ok([_serialize(a) for a in alerts])


@router.put("/alerts/{alert_id}")
def update_alert(alert_id: int, body: dict, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise BusinessError(404, "预警不存在", http_status=404)
    status = body.get("status")
    if status in ("已处理", "已忽略"):
        alert.status = status
        db.commit()
    return ok({"id": alert_id, "status": alert.status})


@router.get("/settings/rules")
def get_rules(db: Session = Depends(get_db)):
    return ok(load_settings(db).get("alert_thresholds", {}))


@router.put("/settings/rules")
def put_rules(body: dict, db: Session = Depends(get_db)):
    current = dict(load_settings(db).get("alert_thresholds", {}))
    current.update(body)
    s = db.get(Setting, "alert_thresholds")
    if s is None:
        s = Setting(key="alert_thresholds")
        db.add(s)
    s.value = current
    s.description = "预警阈值"
    db.commit()
    return ok(current)
