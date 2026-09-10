"""智能问答路由。"""
from pydantic import BaseModel

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ok
from app.services.chat import chat

router = APIRouter()


class ChatRequest(BaseModel):
    text: str


@router.post("/chat")
def chat_endpoint(body: ChatRequest, db: Session = Depends(get_db)):
    return ok(chat(db, body.text))
