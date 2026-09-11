"""通用业务参数设置路由（权重/档位/备货周期/预算/大促日历）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ok
from app.services.settings import load_settings, upsert_setting

router = APIRouter()


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    """返回全部业务参数（含默认值）。"""
    return ok(load_settings(db))


@router.put("/settings")
def put_settings(body: dict, db: Session = Depends(get_db)):
    """部分更新业务参数，body 为 {key: value, ...}。"""
    for key, value in body.items():
        upsert_setting(db, key, value)
    db.commit()
    return ok(load_settings(db))


@router.get("/settings/flags")
def get_flags(db: Session = Depends(get_db)):
    """功能开关读取。"""
    return ok(load_settings(db).get("feature_flags", {}))


@router.put("/settings/flags")
def put_flags(body: dict, db: Session = Depends(get_db)):
    """功能开关更新（部分覆盖）。"""
    current = dict(load_settings(db).get("feature_flags", {}))
    current.update(body)
    upsert_setting(db, "feature_flags", current, "功能开关")
    db.commit()
    return ok(current)
