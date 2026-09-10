"""统一业务异常与响应格式。"""
from typing import Any


class BusinessError(Exception):
    """业务异常：HTTP 状态码 + 业务 code。"""

    def __init__(self, code: int, message: str, http_status: int = 400):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


def ok(data: Any = None, message: str = "ok") -> dict:
    """成功响应统一格式 {code, data, message}。"""
    return {"code": 0, "data": data, "message": message}


def err(code: int, message: str) -> dict:
    """失败响应统一格式。"""
    return {"code": code, "data": None, "message": message}
