"""DeepSeek LLM 客户端（OpenAI 兼容 chat/completions）。

设计：任何异常（无 Key / 网络失败 / 超时 / 返回异常）都返回 None 或空流，由调用方兜底，
保证 AI 问答在 LLM 不可用时仍能给出模板化回答。
"""
import json

import httpx

from app.core.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

MODEL_NAME = DEEPSEEK_MODEL


def _headers() -> dict:
    return {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}


def _messages(system: str, prompt: str) -> list[dict]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]


def generate(system: str, prompt: str, timeout: float = 20.0) -> str | None:
    """非流式调用 DeepSeek 生成回答；失败返回 None（触发兜底）。"""
    if not DEEPSEEK_API_KEY:
        return None
    try:
        resp = httpx.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers=_headers(),
            json={"model": DEEPSEEK_MODEL, "messages": _messages(system, prompt), "temperature": 0.3, "max_tokens": 800},
            timeout=timeout,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return content.strip() or None
    except Exception:
        return None


def stream_generate(system: str, prompt: str, timeout: float = 30.0):
    """流式调用 DeepSeek，逐 token 产出；失败/无 Key 时不产出任何内容（生成器为空）。"""
    if not DEEPSEEK_API_KEY:
        return
    try:
        with httpx.stream(
            "POST",
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers=_headers(),
            json={"model": DEEPSEEK_MODEL, "messages": _messages(system, prompt), "stream": True, "temperature": 0.3},
            timeout=timeout,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = obj["choices"][0].get("delta", {}).get("content", "")
                if delta:
                    yield delta
    except Exception:
        return


def is_available() -> bool:
    """LLM 是否已配置（有 API Key）。"""
    return bool(DEEPSEEK_API_KEY)
