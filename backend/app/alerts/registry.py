"""预警规则注册表：@register_rule 装饰器注册。"""
_RULES: dict[str, dict] = {}


def register_rule(code: str, default_level: str):
    """装饰器：@register_rule(code=..., default_level=...)。"""

    def decorator(fn):
        _RULES[code] = {"code": code, "default_level": default_level, "fn": fn}
        return fn

    return decorator


def list_rules() -> list[dict]:
    return list(_RULES.values())


def get(code: str) -> dict | None:
    return _RULES.get(code)
