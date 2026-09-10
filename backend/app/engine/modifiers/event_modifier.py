"""大促事件修正器：距大促 30~60 天且去年大促热销 ×1.3；普通临近 ×1.1。"""
from datetime import date, timedelta

from app.engine.modifiers import registry
from app.engine.modifiers.base import Modifier
from app.models.daily_sales import DailySales


class EventModifier(Modifier):
    code = "event"
    name = "大促事件"

    def factor(self, sku, ctx: dict) -> tuple[float, str]:
        db = ctx["db"]
        today: date = ctx["calc_date"]
        calendar = ctx["settings"].get("promotion_calendar", [])
        cfg = ctx["settings"]["modifier_tiers"]["event"]

        upcoming = []
        for ev in calendar:
            try:
                d = date.fromisoformat(ev["event_date"])
            except (KeyError, ValueError):
                continue
            if d >= today:
                upcoming.append(d)
        if not upcoming:
            return 1.0, "无临近大促"

        nearest = min(upcoming)
        days = (nearest - today).days

        if 30 <= days <= 60 and self._last_year_hot(db, sku, today, cfg):
            return cfg["hot"], f"距大促{days}天且去年大促热销"
        if days < 30:
            return cfg["near"], f"距大促{days}天，大促临近"
        return 1.0, f"距大促{days}天"

    @staticmethod
    def _last_year_hot(db, sku, today: date, cfg: dict) -> bool:
        """去年 11 月大促窗口日均 > hot_ratio × 近90天日均 视为热销。"""
        year = today.year - 1
        start = date(year, 11, 20)
        end = date(year, 12, 5)
        promo = (
            db.query(DailySales)
            .filter(DailySales.sku == sku.sku, DailySales.date >= start, DailySales.date <= end, DailySales.is_stockout_day.is_(False))
            .all()
        )
        if not promo:
            return False
        promo_avg = sum(r.qty for r in promo) / len(promo)
        recent = (
            db.query(DailySales)
            .filter(DailySales.sku == sku.sku, DailySales.date >= today - timedelta(days=90), DailySales.is_stockout_day.is_(False))
            .all()
        )
        if not recent:
            return False
        recent_avg = sum(r.qty for r in recent) / len(recent)
        return promo_avg > cfg.get("hot_ratio", 1.3) * recent_avg


registry.register(EventModifier())
