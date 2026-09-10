"""环境评分修正器：类目人工评分 -2~+2 线性映射 0.9~1.1。"""
from app.engine.modifiers import registry
from app.engine.modifiers.base import Modifier
from app.models.external_signal import ExternalSignal


class EnvModifier(Modifier):
    code = "env"
    name = "环境评分"

    def factor(self, sku, ctx: dict) -> tuple[float, str]:
        db = ctx["db"]
        sig = (
            db.query(ExternalSignal)
            .filter_by(sku=sku.category, signal_type="env")
            .order_by(ExternalSignal.period.desc())
            .first()
        )
        cfg = ctx["settings"]["modifier_tiers"]["env"]
        if sig is None or sig.value_num is None:
            return 1.0, "环境信号缺失"
        coeff = max(cfg["min"], min(cfg["max"], 1.0 + sig.value_num * 0.05))
        return coeff, f"类目环境评分 {sig.value_num:+.0f}"


registry.register(EnvModifier())
