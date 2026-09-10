"""修正器聚合：导入即注册。可插拔：新增修正器 = 新文件 + 注册。"""
from app.engine.modifiers import base, registry  # noqa: F401
from app.engine.modifiers.trend_modifier import TrendModifier
from app.engine.modifiers.competitor_modifier import CompetitorModifier
from app.engine.modifiers.event_modifier import EventModifier
from app.engine.modifiers.env_modifier import EnvModifier

# 预期修正器清单（注销后按 1.0 降级，供流水线显式记录）
ALL_MODIFIER_CODES = ["trend", "competitor", "event", "env"]

__all__ = [
    "TrendModifier",
    "CompetitorModifier",
    "EventModifier",
    "EnvModifier",
    "ALL_MODIFIER_CODES",
]
