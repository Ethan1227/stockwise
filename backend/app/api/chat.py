"""智能问答路由（普通 + SSE 流式）。"""
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ok
from app.services import llm, qa_router
from app.services.chat import chat

router = APIRouter()


class ChatRequest(BaseModel):
    text: str


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
def chat_endpoint(body: ChatRequest, db: Session = Depends(get_db)):
    return ok(chat(db, body.text))


@router.post("/chat/stream")
def chat_stream(body: ChatRequest, db: Session = Depends(get_db)):
    """SSE 流式问答：先推思考过程，再逐 token 推回答，最后推 chips/actions 与完成事件。

    事件类型：thinking / token / llm / meta / done。
    LLM 不可用时，用模板回答整体推送（token 事件），llm 标记 fallback。
    """
    # 路由 + 思考 + 拉数据（在请求阶段完成，生成器内不再访问 db）
    skill, result, thinking = qa_router.route_and_think(body.text, db)
    system = qa_router.build_system_prompt()
    prompt = qa_router.build_user_prompt(body.text, result)

    def generate():
        yield _sse({"type": "thinking", "content": thinking})
        streamed = False
        for token in llm.stream_generate(system, prompt):
            streamed = True
            yield _sse({"type": "token", "content": token})
        if not streamed:
            # 兜底：LLM 无输出，整体推送模板回答
            yield _sse({"type": "token", "content": result["answer_md"]})
            yield _sse({"type": "llm", "content": "fallback"})
        else:
            yield _sse({"type": "llm", "content": llm.MODEL_NAME})
        yield _sse({"type": "meta", "content": {"data_chips": result.get("data_chips", []), "actions": result.get("actions", [])}})
        yield _sse({"type": "done"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
