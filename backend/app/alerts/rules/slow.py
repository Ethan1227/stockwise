"""滞销预警规则：严重（周转>120 或 库龄>180）、轻度（周转>60 且不严重）。"""
from app.alerts.registry import register_rule


@register_rule(code="slow_severe", default_level="严重")
def slow_severe(sku, cr, inv, settings):
    th = settings["alert_thresholds"]
    turnover = cr.sellable_days
    age = inv.age_days if inv else 0
    if turnover > th["slow_severe_turnover"] or age > th["slow_severe_age"]:
        return {
            "code": "slow_severe",
            "type": "滞销",
            "level": "严重",
            "title": f"{sku.name} 滞销严重",
            "detail": f"周转约 {turnover:.0f} 天，库龄 {age} 天",
            "advice": "建议停止补货，清理库存或促销",
        }
    return None


@register_rule(code="slow_mild", default_level="轻度")
def slow_mild(sku, cr, inv, settings):
    th = settings["alert_thresholds"]
    turnover = cr.sellable_days
    age = inv.age_days if inv else 0
    severe = turnover > th["slow_severe_turnover"] or age > th["slow_severe_age"]
    if not severe and turnover > th["slow_mild_turnover"]:
        return {
            "code": "slow_mild",
            "type": "滞销",
            "level": "轻度",
            "title": f"{sku.name} 滞销轻度",
            "detail": f"周转约 {turnover:.0f} 天",
            "advice": "减少备货量，关注动销",
        }
    return None
