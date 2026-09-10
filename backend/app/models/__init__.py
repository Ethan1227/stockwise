"""ORM 模型聚合：导入即注册到 Base.metadata，供建表与 Alembic 使用。"""
from app.models.sku_master import SkuMaster
from app.models.daily_sales import DailySales
from app.models.inventory_snapshot import InventorySnapshot
from app.models.external_signal import ExternalSignal
from app.models.calc_result import CalcResult
from app.models.suggestion_override import SuggestionOverride
from app.models.alert import Alert
from app.models.purchase_order import PurchaseOrder
from app.models.setting import Setting

__all__ = [
    "SkuMaster",
    "DailySales",
    "InventorySnapshot",
    "ExternalSignal",
    "CalcResult",
    "SuggestionOverride",
    "Alert",
    "PurchaseOrder",
    "Setting",
]
