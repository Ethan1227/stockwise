"""评测数据集（ground truth，以 mock 数据的「内置剧情」为标注来源）。"""
from __future__ import annotations

# 意图识别：问题 -> 预期意图
INTENT_CASES: list[tuple[str, str]] = [
    ("本周要补什么货？", "replenish"),
    ("SK-2087 会断货吗？", "stockout"),
    ("哪些产品滞销？", "slow"),
    ("黑五大促排期？", "promotion"),
    ("生成采购计划", "purchase"),
    ("预算还剩多少？", "budget"),
    ("今天天气怎么样？", "fallback"),
]

# 断货预警：SKU -> 预期等级（紧急/一般/无）
STOCKOUT_TRUTH: dict[str, str] = {
    "SK-2087": "紧急",
    "SK-4419": "一般",
    "SK-7712": "一般",
    "SK-1023": "无", "SK-0561": "无", "SK-8830": "无", "SK-9044": "无", "SK-3302": "无",
}

# 滞销预警：SKU -> 预期等级（严重/轻度/无）
SLOW_TRUTH: dict[str, str] = {
    "SK-0561": "严重",
    "SK-8830": "严重",
    "SK-9044": "轻度",
    "SK-2087": "无", "SK-4419": "无", "SK-7712": "无", "SK-1023": "无", "SK-3302": "无",
}

# 备货评分档：SKU -> 预期分档（立即补货/常规/观望/停止补货）
SCORE_BAND_TRUTH: dict[str, str] = {
    "SK-1023": "立即补货",
    "SK-2087": "常规",
    "SK-4419": "常规",
    "SK-3302": "常规",
    "SK-7712": "观望",
    "SK-0561": "停止补货",
    "SK-8830": "停止补货",
    "SK-9044": "停止补货",
}

# 建议量（是否建议补货）：SKU -> 补货/不补货
SUGGEST_TRUTH: dict[str, str] = {
    "SK-2087": "补货", "SK-4419": "补货", "SK-7712": "补货", "SK-1023": "补货", "SK-3302": "补货",
    "SK-0561": "不补货", "SK-8830": "不补货", "SK-9044": "不补货",
}

ALL_SKUS = list(SCORE_BAND_TRUTH.keys())
