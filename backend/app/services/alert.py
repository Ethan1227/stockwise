"""预警扫描：测算完成后扫描规则，分级预警，去重。"""
from app.alerts import rules as _rules  # noqa: F401  # 注册规则
from app.alerts.notifier import EmailNotifier, notify
from app.alerts.registry import list_rules
from app.models.alert import Alert
from app.models.calc_result import CalcResult
from app.models.inventory_snapshot import InventorySnapshot
from app.models.sku_master import SkuMaster
from app.services.settings import load_settings
from app.services.suggestion import latest_calc_date


def scan_alerts(db) -> int:
    """扫描最新测算结果，创建未处理预警（去重），返回新增条数。"""
    calc_date = latest_calc_date(db)
    if calc_date is None:
        return 0

    settings = load_settings(db)
    results = db.query(CalcResult).filter_by(calc_date=calc_date).all()
    created = 0

    for cr in results:
        sku = db.query(SkuMaster).filter_by(sku=cr.sku).first()
        if sku is None:
            continue
        inv = (
            db.query(InventorySnapshot)
            .filter_by(sku=cr.sku)
            .order_by(InventorySnapshot.date.desc())
            .first()
        )
        for rule in list_rules():
            alert_dict = rule["fn"](sku, cr, inv, settings)
            if alert_dict is None:
                continue
            # 去重：同一 SKU 同 code 未处理的预警不重复创建
            exists = db.query(Alert).filter_by(sku=cr.sku, code=alert_dict["code"], status="未处理").first()
            if exists:
                continue
            alert = Alert(
                sku=cr.sku,
                code=alert_dict["code"],
                alert_type=alert_dict["type"],
                level=alert_dict["level"],
                title=alert_dict["title"],
                detail=alert_dict["detail"],
                advice=alert_dict["advice"],
                status="未处理",
                notify_log={},
            )
            alert.notify_log = notify(alert, settings)
            db.add(alert)
            created += 1

    db.commit()
    return created


def send_daily_digest(db) -> bool:
    """汇总发送未处理的一般/滞销预警邮件，返回是否发送。"""
    settings = load_settings(db)
    cfg = settings.get("smtp", {})
    alerts = db.query(Alert).filter(Alert.status == "未处理", Alert.level != "紧急").all()
    if not alerts:
        return False
    body = "\n\n".join(f"[{a.alert_type}·{a.level}] {a.title}\n{a.detail}\n{a.advice}" for a in alerts)
    email = EmailNotifier()
    ok = email.send_raw(cfg, f"StockWise 预警汇总（{len(alerts)} 条）", body)
    if ok:
        for a in alerts:
            log = dict(a.notify_log or {})
            log["email"] = "digest_sent"
            a.notify_log = log
        db.commit()
    return ok
