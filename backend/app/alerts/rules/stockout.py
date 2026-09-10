"""缺货预警规则：紧急（<安全天数）、一般（<海运头程）。"""
from app.alerts.registry import register_rule


@register_rule(code="stockout_urgent", default_level="紧急")
def stockout_urgent(sku, cr, inv, settings):
    th = settings["alert_thresholds"]
    if cr.sellable_days < th["stockout_urgent_days"]:
        return {
            "code": "stockout_urgent",
            "type": "缺货",
            "level": "紧急",
            "title": f"{sku.name} 缺货紧急",
            "detail": f"可售天数 {cr.sellable_days:.1f} 天，已低于 {th['stockout_urgent_days']} 天",
            "advice": f"立即采购 {cr.suggest_qty} 件，建议改空运",
        }
    return None


@register_rule(code="stockout_normal", default_level="一般")
def stockout_normal(sku, cr, inv, settings):
    th = settings["alert_thresholds"]
    if th["stockout_urgent_days"] <= cr.sellable_days < th["stockout_normal_days"]:
        return {
            "code": "stockout_normal",
            "type": "缺货",
            "level": "一般",
            "title": f"{sku.name} 缺货一般",
            "detail": f"可售天数 {cr.sellable_days:.1f} 天，低于 {th['stockout_normal_days']} 天",
            "advice": f"安排采购 {cr.suggest_qty} 件，海运仍可赶上",
        }
    return None
