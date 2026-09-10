"""竞品情报适配器 -> external_signals(competitor)。"""
import json

from app.datasources import registry
from app.datasources.base import DataSourceAdapter
from app.datasources.utils import load_external_signals


class CompetitorAdapter(DataSourceAdapter):
    source_code = "competitor"
    name = "竞品情报"
    required_columns = ["sku", "competitor_asin", "competitor_name", "status", "price", "rating", "review_growth", "period"]

    def normalize(self, row: dict) -> dict:
        detail = {
            "asin": (row.get("competitor_asin") or "").strip(),
            "name": (row.get("competitor_name") or "").strip(),
            "status": (row.get("status") or "").strip(),
            "price": (row.get("price") or "").strip(),
            "rating": (row.get("rating") or "").strip(),
            "review_growth": (row.get("review_growth") or "").strip(),
        }
        return {
            "sku": (row.get("sku") or "").strip(),
            "value_num": None,
            "value_text": json.dumps(detail, ensure_ascii=False),
            "period": (row.get("period") or "").strip(),
        }

    def load(self, db, records: list[dict]) -> None:
        load_external_signals(db, records, source="competitor", signal_type="competitor")


registry.register(CompetitorAdapter())
