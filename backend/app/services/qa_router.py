"""问答路由编排：技能匹配 -> 思考过程 -> 拉取数据 -> 组装 LLM 上下文。"""
import re

from app.services import llm
from app.services.skill_registry import skill_index, match_skill

SKU_RE = re.compile(r"SK-\d+", re.IGNORECASE)


def _run_handler(code: str | None, text: str, db):
    """按技能码调用对应 handler 拉取数据（复用 chat.py 的 handler）。"""
    from app.services.chat import (
        handle_budget,
        handle_fallback,
        handle_generate_po,
        handle_promotion,
        handle_replenish,
        handle_slow,
        handle_stockout,
    )
    from app.services.settings import load_settings

    settings = load_settings(db)
    sku_codes = [s.upper() for s in SKU_RE.findall(text)]

    if code == "replenish":
        return handle_replenish(db)
    if code == "stockout":
        return handle_stockout(db, sku_codes[0] if sku_codes else None)
    if code == "slow":
        return handle_slow(db)
    if code == "promotion":
        return handle_promotion(settings)
    if code == "purchase":
        return handle_generate_po(db, sku_codes)
    if code == "budget":
        return handle_budget(db, settings)
    return handle_fallback()


def route_and_think(text: str, db) -> tuple[dict | None, dict, list[dict]]:
    """路由 + 拉数据 + 生成思考过程。返回 (skill, result, thinking)。"""
    skill = match_skill(text)
    code = skill["code"] if skill else None

    # 命中关键词（用于思考过程展示）
    matched_kw = [kw for kw in (skill["keywords"] if skill else []) if kw in text]

    result = _run_handler(code, text, db)

    thinking = []
    if skill:
        thinking.append({"step": "意图识别", "detail": f"命中技能「{skill['name']}」（{skill['domain']}）"})
    else:
        thinking.append({"step": "意图识别", "detail": "未命中具体技能，走通用回答"})
    thinking.append({"step": "命中关键词", "detail": "、".join(matched_kw) if matched_kw else "无（通用）"})
    if skill:
        thinking.append(
            {"step": "可查询数据源", "detail": "；".join(d["name"] for d in skill["data_sources"])}
        )
    thinking.append({"step": "数据摘要", "detail": f"拉取 {len(result.get('data_chips', []))} 条结构化数据"})
    thinking.append({"step": "调用模型", "detail": llm.MODEL_NAME})

    return skill, result, thinking


def build_system_prompt() -> str:
    """系统提示词：通用指令 + 技能库索引（告诉 LLM 可查询哪些数据）。"""
    return (
        "你是「智备货 StockWise」的备货决策助手，服务于亚马逊/沃尔玛跨境卖家。\n"
        "你拥有以下可查询的业务数据（技能库）：\n"
        f"{skill_index()}\n"
        "根据给定的业务数据，用简洁自然的简体中文回答用户问题。"
        "不要编造数据；数据里没有的信息就如实说不知道。回答控制在 200 字以内。"
    )


def build_user_prompt(text: str, result: dict) -> str:
    """用户提示词：问题 + 拉取到的业务数据。"""
    return f"用户问题：{text}\n\n业务数据（模板回答）：\n{result['answer_md']}\n\n请基于以上数据用自然语言回答。"
