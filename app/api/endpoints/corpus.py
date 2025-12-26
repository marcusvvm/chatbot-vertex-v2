from fastapi import APIRouter, HTTPException, status, Query, Response, Depends
from typing import List
from app.schemas.corpus import CorpusCreate, CorpusResponse
from app.domain.corpus.service import CorpusService
from google.api_core import exceptions as google_exceptions
from app.core.dependencies import verify_token, get_corpus_service, get_config_service
from app.schemas.auth import TokenData
from app.config.service import ConfigService

router = APIRouter()

@router.post("/corpus", response_model=CorpusResponse, status_code=status.HTTP_201_CREATED)
async def create_corpus(
    corpus: CorpusCreate,
    token_data: TokenData = Depends(verify_token),
    corpus_service: CorpusService = Depends(get_corpus_service)  # ✅ DI
):
    """
    Cria um novo departamento (RAG Corpus) no Vertex AI.
    Automaticamente adiciona o prefixo 'DEP-' ao nome se não estiver presente.
    Esta operação pode levar alguns segundos pois aguarda a confirmação do Google.
    """
    try:
        # Call service
        created_corpus = corpus_service.create_corpus(
            display_name=corpus.department_name,
            description=corpus.description
        )
        
        # Map response to schema
        # High-level SDK returns RagCorpus object which might not have create_time populated immediately
        # or it's not exposed in the preview class.
        corpus_id = created_corpus.name.split('/')[-1]
        
        return CorpusResponse(
            id=corpus_id,
            display_name=created_corpus.display_name,
            name=created_corpus.name,
            create_time=None # Not available in high-level SDK object
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Let the global handler catch it, or re-raise specific HTTP exceptions
        # High-level SDK might raise generic exceptions for API errors
        if "already exists" in str(e).lower():
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Corpus with name '{corpus.department_name}' already exists."
            )
        raise e

@router.get("/corpus", response_model=List[CorpusResponse], status_code=status.HTTP_200_OK)
async def list_corpora(
    token_data: TokenData = Depends(verify_token),
    corpus_service: CorpusService = Depends(get_corpus_service)  # ✅ DI
):
    """
    Lista todos os departamentos (Corpora) do sistema.
    Retorna apenas corpora que começam com 'DEP-'.
    """
    try:
        corpora = corpus_service.list_corpora()
        
        return [
            CorpusResponse(
                id=c.name.split('/')[-1],
                display_name=c.display_name,
                name=c.name,
                create_time=None
            )
            for c in corpora
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao listar departamentos: {str(e)}"
        )

@router.get("/corpus/{corpus_id}/files", status_code=status.HTTP_200_OK)
async def list_corpus_files(
    corpus_id: str,
    token_data: TokenData = Depends(verify_token),
    corpus_service: CorpusService = Depends(get_corpus_service)  # ✅ DI
):
    """
    Lista os arquivos de um departamento (Corpus).
    """
    try:
        files = corpus_service.list_corpus_files(corpus_id=corpus_id)
        
        # Simple mapping for now, we can create a FileResponse schema later
        return [
            {
                "id": f.name.split('/')[-1],
                "display_name": f.display_name,
                "name": f.name,
                # create_time not available in high-level SDK RagFile
                "create_time": None
            }
            for f in files
        ]
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Corpus '{corpus_id}' not found."
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao listar arquivos: {str(e)}"
        )

@router.delete("/corpus/{corpus_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_corpus(
    corpus_id: str,
    confirm: bool = Query(False, description="Confirmação obrigatória para deletar corpus"),
    token_data: TokenData = Depends(verify_token),
    corpus_service: CorpusService = Depends(get_corpus_service),  # ✅ DI
    config_service: ConfigService = Depends(get_config_service)  # ✅ DI for config cleanup
):
    """
    Deleta um corpus inteiro e todos os seus arquivos.
    
    IMPORTANTE: Também deleta a configuração customizada do corpus (se existir)
    para prevenir arquivos órfãos.
    
    Requer confirmação via query param ?confirm=true para segurança.
    
    Args:
        corpus_id: ID do corpus a ser deletado
        confirm: Confirmação obrigatória (deve ser true)
    
    Returns:
        204 No Content (quando confirmado)
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deleção de corpus requer confirmação. Use ?confirm=true"
        )
    
    try:
        # 1. Delete corpus from Vertex AI
        corpus_service.delete_corpus(corpus_id)
        
        # 2. ✅ Delete associated configuration (prevents orphan files)
        config_service.delete_corpus_config(corpus_id)
        # Note: Returns False if config doesn't exist (no problem)
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao deletar corpus: {str(e)}"
        )
