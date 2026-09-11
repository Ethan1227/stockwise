"""功能开关（feature flags）：路由级依赖，开关关闭时返回 403。"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import BusinessError
from app.services.settings import load_settings


def check_feature(name: str):
    """返回一个 FastAPI 依赖：对应功能开关关闭时抛 403。"""

    def dependency(db: Session = Depends(get_db)):
        flags = load_settings(db).get("feature_flags", {})
        if not flags.get(name, True):
            raise BusinessError(403, f"功能已关闭：{name}", http_status=403)

    return dependency
