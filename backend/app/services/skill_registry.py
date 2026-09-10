"""问答路由技能库：定义各业务领域的可查询数据源、关键词、层级关系。

层级：领域(domain) -> 技能(skill) -> 数据源(data_sources，指向 API / 数据表 / MCP 工具)。
AI 问答助手在接到问题时，先读本技能库（skill_index）判断可查询的数据，再按关键词路由。
"""
from __future__ import annotations

# 数据源类型：api（后端 REST 接口）、table（数据库表）、mcp（MCP 工具，预留扩展）
SKILLS: list[dict] = [
    {
        "code": "replenish",
        "name": "备货建议",
        "domain": "测算与建议",
        "keywords": ["补货", "备货", "清单", "进什么货", "要补", "建议"],
        "description": "哪些 SKU 需要补货、建议备货量、评分、可售天数",
        "data_sources": [
            {"type": "table", "name": "calc_result", "desc": "测算结果（预测日销/评分/建议备货量/可售天数）"},
            {"type": "api", "name": "GET /api/suggestions", "desc": "备货建议列表（按评分降序）"},
            {"type": "table", "name": "sku_master", "desc": "商品档案（品名/平台/类目/供应商/MOQ）"},
        ],
    },
    {
        "code": "stockout",
        "name": "断货预测",
        "domain": "预警中心",
        "keywords": ["断货", "缺货", "可售天数", "紧急", "不够卖", "会断"],
        "description": "某 SKU 是否会断货、可售天数、空运/海运建议",
        "data_sources": [
            {"type": "table", "name": "calc_result", "desc": "可售天数 sellable_days、建议备货量 suggest_qty"},
            {"type": "api", "name": "GET /api/alerts?type=缺货", "desc": "缺货预警（紧急/一般）"},
            {"type": "table", "name": "inventory_snapshot", "desc": "分仓库存/在途/库龄"},
        ],
    },
    {
        "code": "slow",
        "name": "滞销分析",
        "domain": "预警中心",
        "keywords": ["滞销", "卖不动", "积压", "周转", "库龄", "卖得慢"],
        "description": "哪些 SKU 滞销、周转天数、库龄、清理建议",
        "data_sources": [
            {"type": "api", "name": "GET /api/alerts?type=滞销", "desc": "滞销预警（严重/轻度）"},
            {"type": "table", "name": "inventory_snapshot", "desc": "库龄 age_days"},
        ],
    },
    {
        "code": "promotion",
        "name": "大促排期",
        "domain": "设置中心",
        "keywords": ["大促", "黑五", "圣诞", "排期", "活动", "入仓截止"],
        "description": "大促日历、入仓截止日、交期倒排",
        "data_sources": [
            {"type": "table", "name": "settings.promotion_calendar", "desc": "大促日历（活动/日期/入仓截止）"},
            {"type": "table", "name": "settings.lead_transit_sea/air", "desc": "海运/空运头程天数"},
        ],
    },
    {
        "code": "purchase",
        "name": "采购计划",
        "domain": "采购管理",
        "keywords": ["采购", "采购单", "下单", "生成采购", "在途", "到货"],
        "description": "采购单生成、状态（草稿/确认/发货/到货）、在途回写",
        "data_sources": [
            {"type": "api", "name": "GET /api/purchase-orders", "desc": "采购单列表（状态/供应商筛选）"},
            {"type": "api", "name": "POST /api/purchase-orders/generate", "desc": "从勾选 SKU 生成草稿"},
            {"type": "table", "name": "purchase_order", "desc": "采购单（po_no/供应商/状态/金额）"},
        ],
    },
    {
        "code": "budget",
        "name": "预算查询",
        "domain": "采购管理",
        "keywords": ["预算", "还剩多少", "花多少", "额度"],
        "description": "月采购预算、当前草稿占用金额",
        "data_sources": [
            {"type": "table", "name": "settings.monthly_budget", "desc": "月采购预算"},
            {"type": "table", "name": "purchase_order(draft)", "desc": "草稿单金额合计"},
        ],
    },
]

SKILL_INDEX_MARKDOWN = "\n".join(
    f"- **{s['name']}**（{s['domain']}）：{s['description']}。数据源："
    + "；".join(f"{d['name']}({d['desc']})" for d in s["data_sources"])
    for s in SKILLS
)


def skill_index() -> str:
    """生成给 LLM 看的技能索引（说明可查询哪些数据）。"""
    return SKILL_INDEX_MARKDOWN


def match_skill(text: str) -> dict | None:
    """按关键词匹配技能（返回第一个命中）。"""
    for s in SKILLS:
        for kw in s["keywords"]:
            if kw in text:
                return s
    return None


def list_skills() -> list[dict]:
    return SKILLS
