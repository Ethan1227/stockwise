"""修正器抽象基类（可插拔契约之二）。"""
from abc import ABC, abstractmethod


class Modifier(ABC):
    code: str = ""   # 修正器码，如 trend/competitor/event/env
    name: str = ""   # 展示名

    @abstractmethod
    def factor(self, sku, ctx: dict) -> tuple[float, str]:
        """返回 (系数, 人话依据)。ctx 含 db/settings/calc_date/base_daily 等。"""
