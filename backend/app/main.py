from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .chat import ChatService
from .models import ChatRequest, ChatResponse, HealthResponse
from .providers import OpenAICompatibleProvider
from .retrieval import RetrievalStore
from .settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    retrieval = RetrievalStore(
        settings.corpus_path,
        settings.embedding_model,
        settings.embedding_cache_path,
    )
    provider = OpenAICompatibleProvider(
        settings.model_base_url,
        settings.model_api_key,
        settings.model_name,
        temperature=settings.model_temperature,
    )
    app.state.retrieval = retrieval
    app.state.provider = provider
    app.state.chat = ChatService(
        retrieval,
        provider,
        settings.retrieval_top_k,
        settings.max_history_messages,
    )
    yield


app = FastAPI(title="InsureTutor API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    retrieval: RetrievalStore = request.app.state.retrieval
    provider: OpenAICompatibleProvider = request.app.state.provider
    return HealthResponse(
        status="ok",
        corpus_chunks=len(retrieval.chunks),
        retrieval_mode=retrieval.mode,
        model_configured=provider.configured,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    service: ChatService = request.app.state.chat
    return await service.answer(payload)


settings = get_settings()
if settings.static_path.exists():
    assets_path = settings.static_path / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}")
    async def frontend(full_path: str):
        candidate = settings.static_path / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(settings.static_path / "index.html")

