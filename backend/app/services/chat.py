"""智能问答：规则化意图识别 + DeepSeek LLM 自然语言生成（LLM 不可用时模板兜底）。"""
import re
from datetime import datetime

from app.models.alert import Alert
from app.models.calc_result import CalcResult
from app.models.purchase_order import PurchaseOrder
from app.models.sku_master import SkuMaster
from app.services import llm, purchase
from app.services.settings import load_settings
from app.services.suggestion import latest_calc_date

SKU_RE = re.compile(r"SK-\d+", re.IGNORECASE)

SUGGESTIONS = [
    "本周要补什么货？",
    "SK-2087 会断货吗？",
    "哪些产品滞销？",
    "黑五大促排期？",
    "生成采购计划",
    "预算还剩多少？",
]


def _ok(answer_md: str, chips=None, actions=None, suggestions=None):
    return {
        "answer_md": answer_md,
        "data_chips": chips or [],
        "actions": actions or [],
        "suggestions": suggestions or [],
    }


def detect_intent(text: str) -> str:
    if "生成采购" in text or "采购计划" in text or "下单" in text:
        return "generate_po"
    if "预算" in text:
        return "budget"
    if "大促" in text or "黑五" in text or "圣诞" in text or "排期" in text:
        return "promotion"
    if "滞销" in text or "卖不动" in text or "积压" in text:
        return "slow"
    if "断货" in text or "缺货" in text:
        return "stockout"
    if "补" in text or "清单" in text or "备货" in text:
        return "replenish"
    return "fallback"


def handle_replenish(db) -> dict:
    calc_date = latest_calc_date(db)
    if calc_date is None:
        return _ok("暂无测算结果，请先执行测算。")
    top = db.query(CalcResult).filter_by(calc_date=calc_date).order_by(CalcResult.score.desc()).limit(5).all()
    lines, chips = [], []
    for cr in top:
        sku = db.query(SkuMaster).filter_by(sku=cr.sku).first()
        name = sku.name if sku else ""
        lines.append(f"- {cr.sku} {name}：建议备货 {cr.suggest_qty} 件（评分 {cr.score}）")
        chips.append({"label": cr.sku, "value": f"{cr.suggest_qty}件"})
    return _ok("本周补货清单（按评分降序）：\n" + "\n".join(lines), chips, [{"type": "link", "label": "查看备货建议", "route": "/suggestions"}])


def handle_stockout(db, sku_code: str | None) -> dict:
    calc_date = latest_calc_date(db)
    if calc_date is None:
        return _ok("暂无测算结果。")
    if sku_code:
        cr = db.query(CalcResult).filter_by(sku=sku_code, calc_date=calc_date).first()
    else:
        cr = db.query(CalcResult).filter_by(calc_date=calc_date).order_by(CalcResult.sellable_days).first()
    if cr is None:
        return _ok("未找到该 SKU 的测算结果。")
    sku = db.query(SkuMaster).filter_by(sku=cr.sku).first()
    name = sku.name if sku else ""
    answer = f"{cr.sku} {name}：可售约 {cr.sellable_days:.1f} 天，建议备货 {cr.suggest_qty} 件。空运约 10 天入仓、海运约 35 天，建议改空运。"
    return _ok(answer, [{"label": cr.sku, "value": f"可售{cr.sellable_days:.1f}天"}])


def handle_slow(db) -> dict:
    alerts = db.query(Alert).filter(Alert.alert_type == "滞销", Alert.status == "未处理").all()
    if not alerts:
        return _ok("暂无滞销预警。")
    lines = [f"- {a.sku}：{a.detail}，{a.advice}" for a in alerts]
    return _ok("滞销原因：\n" + "\n".join(lines), [{"label": a.sku, "value": "滞销"} for a in alerts])


def handle_promotion(settings: dict) -> dict:
    calendar = settings.get("promotion_calendar", [])
    lines = [f"- {ev['event']}：{ev['event_date']}（入仓截止 {ev['warehouse_deadline']}）" for ev in calendar]
    return _ok("大促排期：\n" + "\n".join(lines), [{"label": ev["event"], "value": ev["event_date"]} for ev in calendar])


def handle_generate_po(db, sku_codes: list[str]) -> dict:
    if not sku_codes:
        calc_date = latest_calc_date(db)
        if calc_date:
            top = db.query(CalcResult).filter_by(calc_date=calc_date).order_by(CalcResult.score.desc()).limit(3).all()
            sku_codes = [cr.sku for cr in top]
    orders = purchase.generate_purchase_orders(db, sku_codes)
    if not orders:
        return _ok("未生成采购单（无有效测算结果）。")
    lines = [f"- {o['po_no']}（{o['supplier']}）：{o['total_qty']} 件 ¥{o['total_amount']}" for o in orders]
    return _ok(
        "已生成采购计划：\n" + "\n".join(lines),
        [{"label": o["po_no"], "value": o["supplier"]} for o in orders],
        [{"type": "link", "label": "去采购计划查看", "route": "/purchase"}],
    )


def handle_budget(db, settings: dict) -> dict:
    budget = settings["monthly_budget"]
    drafts = db.query(PurchaseOrder).filter_by(status="draft").all()
    amount = sum(d.total_amount for d in drafts)
    return _ok(
        f"月采购预算 ¥{budget}，当前草稿占用 ¥{amount:.2f}。",
        [{"label": "月预算", "value": f"¥{budget}"}, {"label": "草稿占用", "value": f"¥{amount:.2f}"}],
    )


def handle_fallback() -> dict:
    return _ok("抱歉，我还没理解你的问题。你可以试试：\n" + "\n".join(f"- {s}" for s in SUGGESTIONS), [], [], SUGGESTIONS)


SYSTEM_PROMPT = (
    "你是「智备货 StockWise」的备货决策助手，服务于亚马逊/沃尔玛跨境卖家。"
    "根据提供的业务数据，用简洁自然的简体中文回答用户问题。"
    "不要编造数据；数据里没有的信息就如实说不知道。回答控制在 200 字以内。"
)


def _enhance_with_llm(text: str, result: dict) -> dict:
    """用 LLM 将模板回答改写为自然语言；LLM 不可用/失败时保留模板（兜底）。"""
    template = result["answer_md"]
    enhanced = llm.generate(
        SYSTEM_PROMPT,
        f"用户问题：{text}\n\n业务数据（模板回答）：\n{template}\n\n请基于以上数据用自然语言回答。",
    )
    if enhanced:
        result["answer_md"] = enhanced
        result["llm"] = "deepseek-v4-flash"
    else:
        result["llm"] = "fallback"
    return result


def chat(db, text: str) -> dict:
    intent = detect_intent(text)
    sku_codes = [s.upper() for s in SKU_RE.findall(text)]
    settings = load_settings(db)

    if intent == "replenish":
        result = handle_replenish(db)
    elif intent == "stockout":
        result = handle_stockout(db, sku_codes[0] if sku_codes else None)
    elif intent == "slow":
        result = handle_slow(db)
    elif intent == "promotion":
        result = handle_promotion(settings)
    elif intent == "generate_po":
        result = handle_generate_po(db, sku_codes)
    elif intent == "budget":
        result = handle_budget(db, settings)
    else:
        result = handle_fallback()

    result = _enhance_with_llm(text, result)
    result["answer_md"] += f"\n\n_数据来自今日 {datetime.now().strftime('%H:%M')} 测算，仅供参考_"
    return result
