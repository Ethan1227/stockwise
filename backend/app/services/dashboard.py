"""工作台聚合：KPI、数据源状态、近30天日销序列、待办。"""
from datetime import date, timedelta

from sqlalchemy import func

from app.datasources import registry
from app.models.alert import Alert
from app.models.calc_result import CalcResult
from app.models.daily_sales import DailySales
from app.models.import_log import ImportLog
from app.models.purchase_order import PurchaseOrder
from app.models.sku_master import SkuMaster
from app.services.settings import load_settings
from app.services.suggestion import latest_calc_date


def _sales_series(db, today: date) -> list[dict]:
    start = today - timedelta(days=30)
    rows = db.query(DailySales).filter(DailySales.date >= start).all()
    by_date: dict[str, dict] = {}
    for r in rows:
        d = r.date.isoformat()
        by_date.setdefault(d, {"date": d, "amazon": 0, "walmart": 0})
        by_date[d][r.platform] += r.qty
    return sorted(by_date.values(), key=lambda x: x["date"])


def _todos(db, settings: dict, today: date) -> list[dict]:
    todos: list[dict] = []
    urgent = (
        db.query(Alert)
        .filter(Alert.alert_type == "缺货", Alert.level == "紧急", Alert.status == "未处理")
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )
    for a in urgent:
        todos.append({"type": "紧急缺货", "text": f"{a.title}：{a.advice}", "route": "/alerts"})

    for a in registry.list_adapters():
        last = db.query(ImportLog).filter_by(source_code=a.source_code).order_by(ImportLog.imported_at.desc()).first()
        if last is None or (today - last.imported_at.date()).days > 3:
            todos.append({"type": "数据未更新", "text": f"{a.name} 数据待更新", "route": "/datacenter"})

    drafts = db.query(PurchaseOrder).filter_by(status="draft").all()
    if drafts:
        amount = sum(d.total_amount for d in drafts)
        todos.append({"type": "待确认采购单", "text": f"{len(drafts)} 张草稿待确认，金额 ¥{amount:.2f}", "route": "/purchase"})

    upcoming = []
    for ev in settings.get("promotion_calendar", []):
        try:
            d = date.fromisoformat(ev["event_date"])
            deadline = date.fromisoformat(ev["warehouse_deadline"])
        except (KeyError, ValueError):
            continue
        if d >= today:
            upcoming.append((ev.get("event", "大促"), d, deadline))
    if upcoming:
        name, d, deadline = min(upcoming, key=lambda x: x[1])
        days = (d - today).days
        sea_last_order = deadline - timedelta(days=settings["lead_transit_sea"] + settings["lead_shelf_days"])
        todos.append({"type": "大促", "text": f"{name}倒计时 {days} 天，海运最迟下单日 {sea_last_order}", "route": "/purchase"})

    return todos


def get_summary(db) -> dict:
    settings = load_settings(db)
    today = date.today()
    calc_date = latest_calc_date(db)

    sku_count = db.query(func.count(SkuMaster.sku)).scalar() or 0
    suggest_count = 0
    if calc_date:
        suggest_count = (
            db.query(func.count(CalcResult.id))
            .filter(CalcResult.calc_date == calc_date, CalcResult.suggest_qty > 0)
            .scalar()
            or 0
        )

    stockout = db.query(func.count(Alert.id)).filter(Alert.alert_type == "缺货", Alert.status == "未处理").scalar() or 0
    stockout_urgent = db.query(func.count(Alert.id)).filter(Alert.alert_type == "缺货", Alert.level == "紧急", Alert.status == "未处理").scalar() or 0
    slow = db.query(func.count(Alert.id)).filter(Alert.alert_type == "滞销", Alert.status == "未处理").scalar() or 0

    datasources = []
    for a in registry.list_adapters():
        last = db.query(ImportLog).filter_by(source_code=a.source_code).order_by(ImportLog.imported_at.desc()).first()
        datasources.append(
            {
                "source_code": a.source_code,
                "name": a.name,
                "last_sync": last.imported_at.isoformat() if last else None,
                "status": "已连接" if last else "待更新",
            }
        )

    return {
        "kpi": {
            "sku_count": sku_count,
            "suggest_count": suggest_count,
            "stockout": stockout,
            "stockout_urgent": stockout_urgent,
            "slow": slow,
        },
        "datasources": datasources,
        "sales_series": _sales_series(db, today),
        "todos": _todos(db, settings, today),
    }
