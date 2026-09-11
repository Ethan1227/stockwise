"""RAGAS 评测集：question + 预期意图 + 关键事实（应出现在回答中）。"""
from __future__ import annotations

QA_CASES: list[dict] = [
    {"question": "本周要补什么货？", "skill": "replenish", "facts": ["SK-1023"]},
    {"question": "SK-2087 会断货吗？", "skill": "stockout", "facts": ["SK-2087", "空运"]},
    {"question": "哪些产品滞销？", "skill": "slow", "facts": ["SK-0561"]},
    {"question": "黑五大促排期？", "skill": "promotion", "facts": ["黑五"]},
    {"question": "生成采购计划", "skill": "purchase", "facts": ["采购"]},
    {"question": "预算还剩多少？", "skill": "budget", "facts": ["预算"]},
]
