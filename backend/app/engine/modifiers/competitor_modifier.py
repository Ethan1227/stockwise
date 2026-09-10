"""竞品修正器：主要竞品缺货 +0.1、大幅降价 -0.1。"""
import json

from app.engine.modifiers import registry
from app.engine.modifiers.base import Modifier
from app.models.external_signal import ExternalSignal


class CompetitorModifier(Modifier):
    code = "competitor"
    name = "竞品情报"

    def factor(self, sku, ctx: dict) -> tuple[float, str]:
        db = ctx["db"]
        sigs = db.query(ExternalSignal).filter_by(sku=sku.sku, signal_type="competitor").all()
        tiers = ctx["settings"]["modifier_tiers"]["competitor"]
        if not sigs:
            return 1.0, "竞品信号缺失"

        stockout = False
        price_cut = False
        for s in sigs:
            if not s.value_text:
                continue
            try:
                detail = json.loads(s.value_text)
            except (ValueError, TypeError):
                continue
            status = detail.get("status", "")
            if status == "缺货中":
                stockout = True
            elif status == "大幅降价":
                price_cut = True

        coeff = 1.0
        notes = []
        if stockout:
            coeff += tiers["stockout"]
            notes.append("主要竞品缺货")
        if price_cut:
            coeff += tiers["price_cut"]
            notes.append("竞品大幅降价")
        return coeff, "；".join(notes) if notes else "竞品平稳"


registry.register(CompetitorModifier())
