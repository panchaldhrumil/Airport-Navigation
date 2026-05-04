from pydantic import BaseModel
from typing import Optional


class TextChatRequest(BaseModel):
    session_id: str
    query: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: Optional[str] = None
    language: Optional[str] = None


class AudioChatResponse(BaseModel):
    session_id: str
    response: str
    intent: Optional[str] = None
    language: Optional[str] = None
    transcribed_text: Optional[str] = None