"""亚马逊订单适配器 -> daily_sales。"""
from app.datasources import registry
from app.datasources.base import DataSourceAdapter
from app.datasources.utils import parse_date, parse_float, parse_int
from app.models.daily_sales import DailySales


class AmazonOrdersAdapter(DataSourceAdapter):
    source_code = "amazon_orders"
    name = "亚马逊订单"
    platform = "amazon"
    required_columns = ["sku", "date", "qty", "amount", "is_stockout_day"]

    def normalize(self, row: dict) -> dict:
        return {
            "sku": (row.get("sku") or "").strip(),
            "platform": self.platform,
            "date": parse_date(row.get("date", "")),
            "qty": parse_int(row.get("qty")),
            "amount": parse_float(row.get("amount")),
            "is_stockout_day": str(row.get("is_stockout_day") or "0").strip() in ("1", "true", "True"),
        }

    def validate(self, record: dict) -> list[str]:
        errors = super().validate(record)
        if record["qty"] < 0:
            errors.append("销量为负")
        if record["amount"] < 0:
            errors.append("金额为负")
        return errors

    def load(self, db, records: list[dict]) -> None:
        for r in records:
            obj = db.query(DailySales).filter_by(sku=r["sku"], platform=r["platform"], date=r["date"]).first()
            if obj is None:
                obj = DailySales(sku=r["sku"], platform=r["platform"], date=r["date"])
                db.add(obj)
            obj.qty = r["qty"]
            obj.amount = r["amount"]
            obj.is_stockout_day = r["is_stockout_day"]


registry.register(AmazonOrdersAdapter())
