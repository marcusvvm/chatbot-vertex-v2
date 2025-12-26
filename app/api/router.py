from fastapi import APIRouter
from app.api.endpoints import chat, corpus, documents, config

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(corpus.router, prefix="/management", tags=["management"])  # Mantém /management na URL por compatibilidade
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(config.router, prefix="/config", tags=["configuration"])
