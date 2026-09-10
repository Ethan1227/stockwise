"""工作台路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ok
from app.services.dashboard import get_summary

router = APIRouter()


@router.get("/dashboard/summary")
def summary(db: Session = Depends(get_db)):
    return ok(get_summary(db))
