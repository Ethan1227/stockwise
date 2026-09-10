"""设置读取：settings 表 + 默认值。"""
from app.core.config import DEFAULT_SETTINGS
from app.models.setting import Setting


def load_settings(db) -> dict:
    """读取全部设置（settings 表覆盖默认值）。"""
    result = dict(DEFAULT_SETTINGS)
    for s in db.query(Setting).all():
        result[s.key] = s.value
    return result
