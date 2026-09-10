"""趋势修正器：external_signals(trend) 环比 -> 档位系数。"""
from app.engine.modifiers import registry
from app.engine.modifiers.base import Modifier
from app.models.external_signal import ExternalSignal


class TrendModifier(Modifier):
    code = "trend"
    name = "行情趋势"

    def factor(self, sku, ctx: dict) -> tuple[float, str]:
        db = ctx["db"]
        sig = (
            db.query(ExternalSignal)
            .filter_by(sku=sku.sku, signal_type="trend")
            .order_by(ExternalSignal.period.desc())
            .first()
        )
        if sig is None or sig.value_num is None:
            return 1.0, "趋势信号缺失"
        tiers = ctx["settings"]["modifier_tiers"]["trend"]
        pct = ctx["settings"]["modifier_tiers"]["trend_pct"]
        change = sig.value_num
        if change >= pct["strong_up"]:
            return tiers["strong_up"], f"趋势环比{change:+.0f}%（强升）"
        if change >= pct["up"]:
            return tiers["up"], f"趋势环比{change:+.0f}%（上升）"
        if change <= pct["down"]:
            return tiers["down"], f"趋势环比{change:+.0f}%（下降）"
        return tiers["flat"], f"趋势环比{change:+.0f}%（平稳）"


registry.register(TrendModifier())
