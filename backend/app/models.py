from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8_000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    history: list[ChatMessage] = Field(default_factory=list)
    language: Literal["auto", "en", "zh-CN", "zh-TW"] = "auto"


class Citation(BaseModel):
    id: str
    source: str
    page: int
    section: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    language: str
    grounded: bool
    notice: str | None = None


class HealthResponse(BaseModel):
    status: str
    corpus_chunks: int
    retrieval_mode: str
    model_configured: bool

