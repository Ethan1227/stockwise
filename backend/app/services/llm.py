"""DeepSeek LLM 客户端（OpenAI 兼容 chat/completions）。

设计：任何异常（无 Key / 网络失败 / 超时 / 返回异常）都返回 None，由调用方兜底，
保证 AI 问答在 LLM 不可用时仍能给出模板化回答。
"""
import httpx

from app.core.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


def generate(system: str, prompt: str, timeout: float = 20.0) -> str | None:
    """调用 DeepSeek 生成回答；失败返回 None（触发兜底）。"""
    if not DEEPSEEK_API_KEY:
        return None
    try:
        resp = httpx.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 800,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip() or None
    except Exception:
        return None


def is_available() -> bool:
    """LLM 是否已配置（有 API Key）。"""
    return bool(DEEPSEEK_API_KEY)
