"""一键加载全部 mock 数据：seed + 6 数据源导入 + 历史采购单回填 + 测算 + 预警。

用法：python -m app.core.load_mock
"""
import sys

from app.core.config import PROJECT_ROOT
from app.core.db import Base, SessionLocal, engine
from app.core.seed import seed_default_settings, seed_promotion_calendar, seed_sku_master
from app.datasources import registry
from app.engine.pipeline import run_calc
from app.models.import_log import ImportLog
from app.services.alert import scan_alerts
from app.services.purchase_history import import_purchase_history

# 数据中心 6 个数据源
SOURCES = [
    "amazon_orders",
    "walmart_orders",
    "inventory_snapshot",
    "competitor",
    "trends",
    "env_score",
]

MOCK_DIR = PROJECT_ROOT / "mock"


def main() -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("== seed 基础数据 ==")
        seed_sku_master(db)
        seed_default_settings(db)
        seed_promotion_calendar(db, use_csv=True)
        db.commit()
        print("  sku_master / settings / promotion_calendar 完成")

        print("== 导入 6 个数据源 ==")
        for src in SOURCES:
            result = registry.run(src, db, str(MOCK_DIR / f"{src}.csv"))
            db.add(ImportLog(
                source_code=src,
                filename=f"{src}.csv",
                total_rows=result["total"],
                success_rows=result["success"],
                error_rows=len(result["errors"]),
                error_detail={"errors": result["errors"][:50]},
                operator="load_mock",
            ))
            db.commit()
            print(f"  {src}: 写入 {result['success']} 行，错误 {len(result['errors'])} 条")

        print("== 回填历史采购单 ==")
        n = import_purchase_history(db, str(MOCK_DIR / "purchase_orders_history.csv"))
        db.commit()
        print(f"  历史采购单 {n} 张（shipped 计入在途）")

        print("== 测算 + 预警 ==")
        calc = run_calc(db)
        alerts = scan_alerts(db)
        print(f"  测算 {calc['count']} 个 SKU，新增预警 {alerts} 条")
    finally:
        db.close()
    print("mock 数据加载完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
