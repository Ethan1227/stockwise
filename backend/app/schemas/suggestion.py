"""备货建议相关 Pydantic 模型。"""
from pydantic import BaseModel


class SuggestionUpdate(BaseModel):
    """人工改量或忽略。adjusted_qty 为 None 表示忽略。"""

    adjusted_qty: int | None = None
    note: str = ""
