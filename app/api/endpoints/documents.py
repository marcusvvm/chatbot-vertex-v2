from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from app.schemas.document import DocumentUploadResponse
from app.domain.documents.service import DocumentService
from app.core.dependencies import verify_token, get_document_service
from app.schemas.auth import TokenData
from google.api_core import exceptions as google_exceptions
import tempfile
import os

router = APIRouter()

# Validações
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB (limite do SDK de alto nível)

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    corpus_id: str = Form(...),
    user_id: str = Form(...),
    token_data: TokenData = Depends(verify_token),
    document_service: DocumentService = Depends(get_document_service)  # ✅ DI
):
    """
    Upload de documento diretamente para Vertex AI RAG (até 25MB).
    
    Args:
        file: Arquivo para upload (PDF, TXT, DOCX, MD)
        corpus_id: ID do corpus onde o arquivo será importado
    
    Returns:
        DocumentUploadResponse com detalhes do arquivo importado
    """
    # Validação de extensão
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de arquivo não suportado. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validação de tamanho
    file.file.seek(0, 2)  # Move to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Arquivo muito grande. Máximo: 25MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo vazio"
        )
    
    tmp_path = None
    try:
        # Salvar arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Upload direto para Vertex AI usando SDK de alto nível
        rag_file = document_service.upload_file(
            corpus_id=corpus_id,
            file_path=tmp_path,
            display_name=file.filename,
            description=f"Uploaded by user {token_data.sub}"
        )
        
        # Extrair ID do resource name
        # Format: projects/.../locations/.../ragCorpora/.../ragFiles/{file_id}
        rag_file_id = rag_file.name.split('/')[-1]
        
        return DocumentUploadResponse(
            rag_file_id=rag_file_id,
            gcs_uri=rag_file.name,  # Full resource name
            display_name=file.filename,
            corpus_id=corpus_id,
            status="uploaded"
        )
    
    except RuntimeError as e:
        # Vertex AI RAG SDK raises RuntimeError for non-existent corpus
        # Error format: ('Failed in indexing the RagFile due to: ', {'code': 400, 'message': '...', 'status': 'INVALID_ARGUMENT'})
        error_str = str(e)
        if 'INVALID_ARGUMENT' in error_str or 'invalid argument' in error_str.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Corpus '{corpus_id}' não encontrado"
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao processar upload: {error_str}"
        )
    except Exception as e:
        # Generic handler for other errors
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao processar upload: {str(e)}"
        )
    
    finally:
        # Limpar arquivo temporário
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass  # Ignore cleanup errors

@router.delete("/{corpus_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    corpus_id: str,
    file_id: str,
    token_data: TokenData = Depends(verify_token),
    document_service: DocumentService = Depends(get_document_service)  # ✅ DI
):
    """
    Deleta um arquivo específico de um corpus.
    Operação idempotente - sempre retorna 204, mesmo se arquivo não existir.
    
    Args:
        corpus_id: ID do corpus
        file_id: ID do arquivo a ser deletado
    
    Returns:
        204 No Content (sempre)
    """
    try:
        document_service.delete_file(corpus_id, file_id)
        from fastapi import Response
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        # Apenas erros não relacionados a "not found"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao deletar arquivo: {str(e)}"
        )

@router.get("/{corpus_id}/files/{file_id}", status_code=status.HTTP_200_OK)
async def get_document(
    corpus_id: str,
    file_id: str,
    token_data: TokenData = Depends(verify_token),
    document_service: DocumentService = Depends(get_document_service)  # ✅ DI
):
    """
    Retorna detalhes de um arquivo específico, incluindo status.
    
    Args:
        corpus_id: ID do corpus
        file_id: ID do arquivo
    
    Returns:
        Objeto com detalhes do arquivo
    """
    try:
        rag_file = document_service.get_file(corpus_id, file_id)
        
        # Map RagFile object to dict
        return {
            "id": rag_file.name.split('/')[-1],
            "display_name": rag_file.display_name,
            "name": rag_file.name,
            "create_time": str(rag_file.create_time) if hasattr(rag_file, 'create_time') else None,
            "update_time": str(rag_file.update_time) if hasattr(rag_file, 'update_time') else None,
        }
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "404" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo '{file_id}' não encontrado no corpus '{corpus_id}'."
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao recuperar arquivo: {str(e)}"
        )
