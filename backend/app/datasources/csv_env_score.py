"""环境评分适配器 -> external_signals(env)。类目级信号，类目名存入 sku 字段。"""
from app.datasources import registry
from app.datasources.base import DataSourceAdapter
from app.datasources.utils import load_external_signals, parse_float


class EnvScoreAdapter(DataSourceAdapter):
    source_code = "env_score"
    name = "环境评分"
    required_columns = ["category", "score", "note", "period"]

    def normalize(self, row: dict) -> dict:
        return {
            "sku": (row.get("category") or "").strip(),  # 类目名（env 为类目级）
            "value_num": parse_float(row.get("score")),
            "value_text": (row.get("note") or "").strip(),
            "period": (row.get("period") or "").strip(),
        }

    def load(self, db, records: list[dict]) -> None:
        load_external_signals(db, records, source="env_score", signal_type="env")


registry.register(EnvScoreAdapter())
