"""库存报告适配器 -> inventory_snapshot。"""
from app.datasources import registry
from app.datasources.base import DataSourceAdapter
from app.datasources.utils import parse_date, parse_int
from app.models.inventory_snapshot import InventorySnapshot


class InventoryAdapter(DataSourceAdapter):
    source_code = "inventory_snapshot"
    name = "库存报告"
    required_columns = ["sku", "date", "fba_qty", "wfs_qty", "cn_qty", "in_transit_qty", "age_days"]

    def normalize(self, row: dict) -> dict:
        return {
            "sku": (row.get("sku") or "").strip(),
            "date": parse_date(row.get("date", "")),
            "fba_qty": parse_int(row.get("fba_qty")),
            "wfs_qty": parse_int(row.get("wfs_qty")),
            "cn_qty": parse_int(row.get("cn_qty")),
            "in_transit_qty": parse_int(row.get("in_transit_qty")),
            "age_days": parse_int(row.get("age_days")),
        }

    def validate(self, record: dict) -> list[str]:
        errors = super().validate(record)
        for k in ("fba_qty", "wfs_qty", "cn_qty", "in_transit_qty", "age_days"):
            if record[k] < 0:
                errors.append(f"{k} 为负")
                break
        return errors

    def load(self, db, records: list[dict]) -> None:
        for r in records:
            obj = db.query(InventorySnapshot).filter_by(sku=r["sku"], date=r["date"]).first()
            if obj is None:
                obj = InventorySnapshot(sku=r["sku"], date=r["date"])
                db.add(obj)
            obj.fba_qty = r["fba_qty"]
            obj.wfs_qty = r["wfs_qty"]
            obj.cn_qty = r["cn_qty"]
            obj.in_transit_qty = r["in_transit_qty"]
            obj.age_days = r["age_days"]


registry.register(InventoryAdapter())
