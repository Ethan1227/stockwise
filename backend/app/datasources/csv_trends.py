"""行情趋势适配器 -> external_signals(trend)。"""
from app.datasources import registry
from app.datasources.base import DataSourceAdapter
from app.datasources.utils import load_external_signals


class TrendsAdapter(DataSourceAdapter):
    source_code = "trends"
    name = "行情趋势"
    required_columns = ["sku", "keyword", "index_30d", "index_prev30d", "change", "period"]

    def normalize(self, row: dict) -> dict:
        change = (row.get("change") or "").strip()  # 如 "+35%" / "-18%"
        num = 0.0
        try:
            num = float(change.replace("%", "").strip())
        except ValueError:
            num = 0.0
        return {
            "sku": (row.get("sku") or "").strip(),
            "value_num": num,
            "value_text": change,
            "period": (row.get("period") or "").strip(),
        }

    def load(self, db, records: list[dict]) -> None:
        load_external_signals(db, records, source="trends", signal_type="trend")


registry.register(TrendsAdapter())
