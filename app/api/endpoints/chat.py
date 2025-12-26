from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.domain.chat.service import ChatService
from app.core.dependencies import verify_token, get_chat_service, get_chat_executor
from app.schemas.auth import TokenData
from google.genai import errors as genai_errors
from concurrent.futures import ThreadPoolExecutor
import asyncio

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    token_data: TokenData = Depends(verify_token),
    chat_service: ChatService = Depends(get_chat_service),
    executor: ThreadPoolExecutor = Depends(get_chat_executor)
):
    """
    Endpoint para chat com RAG (Retrieval Augmented Generation).
    
    Uses dynamic configuration per corpus from ConfigService.
    """
    try:
        # Convert Pydantic models to dicts
        history_dicts = [msg.model_dump() for msg in request.history]
        
        # Get event loop
        loop = asyncio.get_event_loop()
        
        # Call service (runs in custom thread pool with 50 workers)
        response_text = await asyncio.wait_for(
            loop.run_in_executor(
                executor,
                lambda: chat_service.chat_rag(
                    message=request.message,
                    history=history_dicts,
                    corpus_id=request.corpus_id
                )
            ),
            timeout=120.0  # Max timeout, actual timeout is per-corpus config
        )
        
        # Update history
        new_history = request.history.copy()
        new_history.append(Message(role="user", content=request.message))
        new_history.append(Message(role="model", content=response_text))
        
        return ChatResponse(
            response=response_text,
            new_history=new_history
        )
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Tempo limite excedido ao aguardar resposta da IA."
        )
    except genai_errors.ClientError as e:
        error_str = str(e)
        if 'invalid rag corpus' in error_str.lower() or 'INVALID_ARGUMENT' in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Corpus não found encontrado: {request.corpus_id}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar chat: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado: {str(e)}"
        )
