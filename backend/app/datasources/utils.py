"""数据源解析工具函数。"""
from datetime import date, datetime

from app.models.external_signal import ExternalSignal


def parse_date(s) -> date:
    """解析 YYYY-MM-DD，非法则抛 ValueError（由 registry 捕获进错误报告）。"""
    return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()


def parse_int(s, default: int = 0) -> int:
    try:
        return int(float(str(s)))
    except (TypeError, ValueError):
        return default


def parse_float(s, default: float = 0.0) -> float:
    try:
        return float(str(s))
    except (TypeError, ValueError):
        return default


def load_external_signals(db, records: list[dict], source: str, signal_type: str) -> None:
    """将外部信号写入 external_signals：按 source+period 删除旧值后重插（幂等覆盖）。"""
    periods = {r["period"] for r in records}
    for p in periods:
        db.query(ExternalSignal).filter_by(source=source, period=p).delete()
    for r in records:
        db.add(ExternalSignal(
            sku=r["sku"],
            signal_type=signal_type,
            value_num=r.get("value_num"),
            value_text=r.get("value_text"),
            period=r["period"],
            source=source,
        ))
