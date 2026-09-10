"""修正器注册表。"""
from app.engine.modifiers.base import Modifier

_MODIFIERS: dict[str, Modifier] = {}


def register(modifier: Modifier) -> None:
    _MODIFIERS[modifier.code] = modifier


def get(code: str) -> Modifier | None:
    return _MODIFIERS.get(code)


def list_modifiers() -> list[Modifier]:
    return list(_MODIFIERS.values())


def unregister(code: str) -> None:
    """注销修正器（降级验证用）。"""
    _MODIFIERS.pop(code, None)
