"""设置读取与写入：settings 表 + 默认值。"""
from app.core.config import DEFAULT_SETTINGS
from app.models.setting import Setting


def load_settings(db) -> dict:
    """读取全部设置（settings 表覆盖默认值）。"""
    result = dict(DEFAULT_SETTINGS)
    for s in db.query(Setting).all():
        result[s.key] = s.value
    return result


def upsert_setting(db, key: str, value, description: str = "") -> Setting:
    """按主键 upsert 一条设置。"""
    obj = db.get(Setting, key)
    if obj is None:
        obj = Setting(key=key, value=value, description=description)
        db.add(obj)
    else:
        obj.value = value
        obj.description = description
    return obj
