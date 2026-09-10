"""种子脚本：python -m app.core.seed --mock

阶段 0 导入内容：
- sku_master.csv -> sku_master（8 个商品档案）
- promotion_calendar.csv -> settings["promotion_calendar"]（以 CSV 为准）
- DEFAULT_SETTINGS -> settings（权重/档位/阈值/预算等默认值）

订单/库存/竞品/趋势/环境数据由阶段 1 的上传 API 导入，不在 seed 范围内。
"""
import argparse
import csv
import sys
from pathlib import Path

from app.core.config import DEFAULT_SETTINGS, PROJECT_ROOT
from app.core.db import Base, SessionLocal, engine
import app.models  # noqa: F401  # 注册全部模型

MOCK_DIR = PROJECT_ROOT / "mock"


def read_csv_rows(path: Path) -> list[dict]:
    """读取 CSV（UTF-8 带 BOM），返回有效字典行列表。"""
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [row for row in csv.DictReader(f) if row.get("sku") or row.get("event")]


def _upsert_setting(db, key: str, value, description: str = ""):
    """按主键 upsert 一条设置（get 命中则更新，否则新增，避免重复插入）。"""
    from app.models.setting import Setting
    obj = db.get(Setting, key)
    if obj is None:
        obj = Setting(key=key, value=value, description=description)
        db.add(obj)
    else:
        obj.value = value
        obj.description = description
    return obj


def seed_sku_master(db) -> int:
    from app.models.sku_master import SkuMaster
    rows = read_csv_rows(MOCK_DIR / "sku_master.csv")
    for r in rows:
        sku = r["sku"].strip()
        obj = db.get(SkuMaster, sku)
        if obj is None:
            obj = SkuMaster(sku=sku)
            db.add(obj)
        obj.name = r["name"].strip()
        obj.platform = (r.get("platform") or "").strip()
        obj.category = (r.get("category") or "").strip()
        obj.supplier = (r.get("supplier") or "").strip()
        obj.unit_cost = float(r.get("unit_cost") or 0)
        obj.price = float(r.get("price") or 0)
        obj.moq = int(r.get("moq") or 1)
        obj.lead_prod_days = int(r.get("lead_prod_days") or 0)
        obj.lead_ship_days = int(r.get("lead_ship_days") or 35)
        obj.safety_days = int(r.get("safety_days") or 10)
    return len(rows)


def seed_default_settings(db) -> int:
    descriptions = {
        "base_weights": "基线日销权重 30d/90d/yoy",
        "safety_days": "安全天数",
        "lead_transit_sea": "头程海运天数",
        "lead_transit_air": "头程空运天数",
        "lead_shelf_days": "上架天数",
        "monthly_budget": "月采购预算",
        "alert_thresholds": "预警阈值",
        "modifier_tiers": "四修正器档位",
    }
    # 跳过 promotion_calendar（由 seed_promotion_calendar 单独写入，避免同键重复插入）
    for key, value in DEFAULT_SETTINGS.items():
        if key == "promotion_calendar":
            continue
        _upsert_setting(db, key, value, descriptions.get(key, ""))
    return len(DEFAULT_SETTINGS) - 1


def seed_promotion_calendar(db, use_csv: bool) -> int:
    path = MOCK_DIR / "promotion_calendar.csv"
    if use_csv and path.exists():
        rows = read_csv_rows(path)
        calendar = [
            {
                "event": r["event"].strip(),
                "event_date": r["event_date"].strip(),
                "warehouse_deadline": r["warehouse_deadline"].strip(),
            }
            for r in rows
        ]
    else:
        calendar = DEFAULT_SETTINGS["promotion_calendar"]
    # 以 CSV 为准覆盖默认大促日历
    _upsert_setting(db, "promotion_calendar", calendar, "大促日历")
    return len(calendar)


def main() -> int:
    parser = argparse.ArgumentParser(description="StockWise 种子脚本")
    parser.add_argument("--mock", action="store_true", help="导入 mock 模拟数据")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)  # 首次启动自动建表

    db = SessionLocal()
    try:
        counts = {
            "settings": seed_default_settings(db),
            "promotion_calendar": seed_promotion_calendar(db, use_csv=args.mock),
        }
        if args.mock:
            counts["sku_master"] = seed_sku_master(db)
        db.commit()
        print("seed 完成：", counts)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
