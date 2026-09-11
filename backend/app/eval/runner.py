"""评测 runner：对意图识别 / 断货预警 / 滞销预警 / 评分档 / 建议量 计算分类指标。"""
from app.eval.dataset import (
    ALL_SKUS,
    INTENT_CASES,
    SCORE_BAND_TRUTH,
    SLOW_TRUTH,
    STOCKOUT_TRUTH,
    SUGGEST_TRUTH,
)
from app.eval.metrics import classification_metrics
from app.models.alert import Alert
from app.models.calc_result import CalcResult
from app.services.suggestion import latest_calc_date


def evaluate_intent(db) -> dict:
    from app.services.skill_registry import match_skill

    y_true, y_pred = [], []
    for text, expected in INTENT_CASES:
        skill = match_skill(text)
        y_true.append(expected)
        y_pred.append(skill["code"] if skill else "fallback")
    return classification_metrics(y_true, y_pred)


def _system_alert_level(db, alert_type: str) -> dict[str, str]:
    """系统输出：未处理预警中，每个 SKU 的最高等级。"""
    alerts = db.query(Alert).filter(Alert.alert_type == alert_type, Alert.status == "未处理").all()
    level: dict[str, str] = {}
    for a in alerts:
        cur = level.get(a.sku)
        # 缺货：紧急 > 一般；滞销：严重 > 轻度
        if cur is None or _rank(a.level) > _rank(cur):
            level[a.sku] = a.level
    return level


def _rank(level: str) -> int:
    return {"紧急": 3, "严重": 3, "一般": 2, "轻度": 1}.get(level, 0)


def evaluate_stockout(db) -> dict:
    sys_level = _system_alert_level(db, "缺货")
    y_true, y_pred = [], []
    for sku, expected in STOCKOUT_TRUTH.items():
        y_true.append(expected)
        y_pred.append(sys_level.get(sku, "无"))
    return classification_metrics(y_true, y_pred)


def evaluate_slow(db) -> dict:
    sys_level = _system_alert_level(db, "滞销")
    y_true, y_pred = [], []
    for sku, expected in SLOW_TRUTH.items():
        y_true.append(expected)
        y_pred.append(sys_level.get(sku, "无"))
    return classification_metrics(y_true, y_pred)


def evaluate_score_band(db) -> dict:
    calc_date = latest_calc_date(db)
    band = {}
    if calc_date:
        rows = db.query(CalcResult).filter(CalcResult.calc_date == calc_date).all()
        band = {r.sku: r.score_band for r in rows}
    y_true, y_pred = [], []
    for sku, expected in SCORE_BAND_TRUTH.items():
        y_true.append(expected)
        y_pred.append(band.get(sku, "无"))
    return classification_metrics(y_true, y_pred)


def evaluate_suggest(db) -> dict:
    calc_date = latest_calc_date(db)
    qty = {}
    if calc_date:
        rows = db.query(CalcResult).filter(CalcResult.calc_date == calc_date).all()
        qty = {r.sku: ("补货" if r.suggest_qty > 0 else "不补货") for r in rows}
    y_true, y_pred = [], []
    for sku, expected in SUGGEST_TRUTH.items():
        y_true.append(expected)
        y_pred.append(qty.get(sku, "不补货"))
    return classification_metrics(y_true, y_pred)


def run_all(db) -> dict:
    """跑全部评测，返回 {功能: 指标}。"""
    return {
        "intent": evaluate_intent(db),
        "stockout": evaluate_stockout(db),
        "slow": evaluate_slow(db),
        "score_band": evaluate_score_band(db),
        "suggest": evaluate_suggest(db),
    }
