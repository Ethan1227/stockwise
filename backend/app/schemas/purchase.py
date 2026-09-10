"""采购计划相关 Pydantic 模型。"""
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    skus: list[str]
