"""数据源适配器：导入本包即完成注册（可插拔，新增适配器 = 新文件 + registry 一行注册）。"""
from app.datasources import base, registry  # noqa: F401
from app.datasources.csv_amazon_orders import AmazonOrdersAdapter
from app.datasources.csv_walmart_orders import WalmartOrdersAdapter
from app.datasources.csv_inventory import InventoryAdapter
from app.datasources.csv_competitor import CompetitorAdapter
from app.datasources.csv_trends import TrendsAdapter
from app.datasources.csv_env_score import EnvScoreAdapter

__all__ = [
    "AmazonOrdersAdapter",
    "WalmartOrdersAdapter",
    "InventoryAdapter",
    "CompetitorAdapter",
    "TrendsAdapter",
    "EnvScoreAdapter",
]
