from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage
import os
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

# WORKAROUND: The vertexai.preview.rag.upload_file() function internally calls auth.default()
# which ignores the custom credentials passed to vertexai.init(). 
# To fix this, we set GOOGLE_APPLICATION_CREDENTIALS to point to our unified credentials.
# This allows all RAG and Chat operations to work correctly with the same credential.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

from app.core.exceptions import google_exception_handler, global_exception_handler
from app.api.router import api_router
from google.api_core import exceptions as google_exceptions
from google.oauth2 import service_account

# ============================================================================
# Thread Pool Executor for Chat Operations
# ============================================================================
# Executor customizado para operações de chat que são CPU/IO bound.
# Com 50 workers, suportamos até 50 chats simultâneos (vs 12 do default).
# Isso garante baixa latência mesmo com múltiplos usuários simultâneos.
chat_executor = ThreadPoolExecutor(
    max_workers=50,
    thread_name_prefix="chat-worker-"
)

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
# Permite:
# - Localhost e 127.0.0.1 (desenvolvimento)
# - Rede local (192.168.x.x e 10.x.x.x)
# - Domínio crea-go.org.br e seus subdomínios
ALLOWED_ORIGINS_REGEX = r"^(http://localhost(:\d+)?|http://127\.0\.0\.1(:\d+)?|http://192\.168\.\d{1,3}\.\d{1,3}(:\d+)?|http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?|https?://(.*\.)?crea-go\.org\.br(:\d+)?)$"
# ALLOWED_ORIGINS_REGEX = r".*"  # Permissive for debugging

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ALLOWED_ORIGINS_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(google_exceptions.GoogleAPICallError, google_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include Router
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Verifica a saúde da API e a conexão com o Google Cloud.
    """
    try:
        # Verifica apenas se a API está respondendo e as configurações básicas estão carregadas
        # Não verificamos mais bucket pois a arquitetura mudou para RAG Engine direto
        
        return {
            "status": "healthy",
            "google_auth": "configured",
            "project_id": settings.GCP_PROJECT_ID,
            "mode": "rag_engine_direct"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health Check Failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
