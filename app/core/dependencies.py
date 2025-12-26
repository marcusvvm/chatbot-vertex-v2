from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.core.auth import decode_token
from app.schemas.auth import TokenData
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Imports para Dependency Injection
from app.infrastructure.gcp.client import GCPClient
from app.domain.corpus.service import CorpusService
from app.domain.documents.service import DocumentService
from app.domain.chat.service import ChatService

# Security scheme para Swagger UI
security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency para validar token JWT em endpoints protegidos.
    
    Uso:
        @router.post("/corpus")
        async def create_corpus(
            corpus: CorpusCreate,
            token_data: TokenData = Depends(verify_token)
        ):
            ...
    
    Raises:
        HTTPException 401: Token inválido ou ausente
    """
    token = credentials.credentials
    
    try:
        token_data = decode_token(token)
        return token_data
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Dependency opcional para logging (futuro)
async def get_current_user(
    token_data: TokenData = Depends(verify_token)
) -> str:
    """Retorna o subject do token para logging"""
    return token_data.sub


# ============================================================================
# Dependency Injection - Infrastructure e Domain Services
# ============================================================================

@lru_cache()
def get_gcp_client() -> GCPClient:
    """
    Retorna instância singleton de GCPClient.
    
    O decorator @lru_cache garante que apenas uma instância
    é criada e compartilhada entre todas as requisições.
    
    Returns:
        GCPClient singleton com credenciais GCP
    """
    return GCPClient()


@lru_cache()
def get_corpus_service() -> CorpusService:
    """
    Retorna instância singleton de CorpusService.
    
    Uso em endpoints:
        @router.post("/corpus")
        async def create_corpus(
            service: CorpusService = Depends(get_corpus_service)
        ):
            corpus = service.create_corpus(...)
    
    Returns:
        CorpusService configurado com GCPClient
    """
    return CorpusService(get_gcp_client())


@lru_cache()
def get_document_service() -> DocumentService:
    """
    Retorna instância singleton de DocumentService.
    
    Uso em endpoints:
        @router.post("/upload")
        async def upload(
            service: DocumentService = Depends(get_document_service)
        ):
            file = service.upload_file(...)
    
    Returns:
        DocumentService configurado com GCPClient
    """
    return DocumentService(get_gcp_client())


@lru_cache()
def get_chat_service() -> ChatService:
    """
    Retorna instância singleton de ChatService.
    
    ChatService now uses ConfigService for dynamic configuration.
    
    Uso em endpoints:
        @router.post("/chat")
        async def chat(
            service: ChatService = Depends(get_chat_service)
        ):
            response = service.chat_rag(...)
    
    Returns:
        ChatService configurado com GCPClient e ConfigService
    """
    return ChatService(
        gcp_client=get_gcp_client(),
        config_service=get_config_service()
    )


@lru_cache()
def get_config_service() -> 'ConfigService':
    """
    Retorna instância singleton de ConfigService.
    
    ConfigService gerencia configurações dinâmicas por corpus.
    
    Uso em endpoints:
        @router.get("/config/corpus/{corpus_id}")
        async def get_config(
            config_service: ConfigService = Depends(get_config_service)
        ):
            config = config_service.get_merged_config(corpus_id)
    
    Returns:
        ConfigService com config_dir="config"
    """
    from app.config.service import ConfigService
    return ConfigService(config_dir="config")


def get_chat_executor() -> ThreadPoolExecutor:
    """
    Retorna executor customizado para operações de chat.
    
    Thread pool com 50 workers para garantir alta concorrência
    em operações de chat (que são síncronas/bloqueantes).
    
    Uso em endpoints:
        @router.post("/chat")
        async def chat(
            executor: ThreadPoolExecutor = Depends(get_chat_executor)
        ):
            result = await loop.run_in_executor(executor, sync_function)
    
    Returns:
        ThreadPoolExecutor com 50 workers
    """
    from app.main import chat_executor
    return chat_executor
