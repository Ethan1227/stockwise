"""备货评分：缺货紧迫 40 + 销售健康 25 + 外部信号 25 + 资金效率 10。"""


def compute_score(sku, forecast: float, factors: dict, sellable_days: float, lead_shelf_days: int) -> tuple[int, dict]:
    lead_cycle = sku.lead_prod_days + sku.lead_ship_days + lead_shelf_days + sku.safety_days

    # 1. 缺货紧迫（40）：可售天数越短越紧迫
    urgency = 40 * max(0.0, min(1.0, (lead_cycle - sellable_days) / lead_cycle)) if lead_cycle > 0 else 0.0

    # 2. 销售健康（25）：趋势档位
    trend = factors.get("trend", 1.0)
    health = 25 * max(0.0, min(1.0, 0.5 + (trend - 1.0) * 1.5))

    # 3. 外部信号（25）：综合系数偏离
    product = 1.0
    for c in factors.values():
        product *= c
    signal = 25 * max(0.0, min(1.0, 0.5 + (product - 1.0) * 1.5))

    # 4. 资金效率（10）：毛利率
    margin = (sku.price - sku.unit_cost) / sku.price if sku.price > 0 else 0.0
    capital = 10 * max(0.0, min(1.0, margin))

    score = round(urgency + health + signal + capital)
    detail = {
        "缺货紧迫": {"score": round(urgency, 1), "max": 40},
        "销售健康": {"score": round(health, 1), "max": 25},
        "外部信号": {"score": round(signal, 1), "max": 25},
        "资金效率": {"score": round(capital, 1), "max": 10},
    }
    return score, detail


def score_band(score: int) -> str:
    if score >= 80:
        return "立即补货"
    if score >= 60:
        return "常规"
    if score >= 40:
        return "观望"
    return "停止补货"
