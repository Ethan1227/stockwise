"""数据源适配器抽象基类（可插拔契约之一）。"""
import csv
from abc import ABC, abstractmethod


class DataSourceAdapter(ABC):
    """数据源适配器：source_code / fetch / normalize / validate / load。"""

    source_code: str = ""   # 唯一标识，如 amazon_orders
    name: str = ""          # 展示名，如「亚马逊订单」
    required_columns: list[str] = []  # 表头必填列（缺列则 400）

    def fetch(self, path: str) -> list[dict]:
        """读取 CSV（UTF-8 带 BOM），返回原始行列表（过滤全空行）。"""
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        return [r for r in rows if any((v or "").strip() for v in r.values())]

    @abstractmethod
    def normalize(self, row: dict) -> dict:
        """原始行 -> 标准记录 dict。"""

    def validate(self, record: dict) -> list[str]:
        """校验标准记录，返回错误信息列表（空 = 通过）。"""
        errors: list[str] = []
        if not record.get("sku"):
            errors.append("缺少 SKU")
        return errors

    @abstractmethod
    def load(self, db, records: list[dict]) -> None:
        """将校验通过的记录写入标准表（幂等：覆盖不重复）。"""
