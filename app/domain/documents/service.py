"""
Document Service - Gerencia upload e operações com arquivos.

Este módulo implementa a lógica de negócio para upload, deleção
e consulta de arquivos RAG no Vertex AI.

Single Responsibility: Apenas operações de Documents/Files.
"""

from vertexai.preview import rag
from typing import Any
from app.infrastructure.gcp.client import GCPClient


class DocumentService:
    """
    Service para gerenciar documentos (RAG Files).
    
    Responsabilidades:
    - Upload de arquivos para corpus
    - Deleção de arquivos (idempotente)
    - Consulta de detalhes de arquivo
    
    Dependencies:
    - GCPClient: Autenticação e helpers
    """
    
    def __init__(self, gcp_client: GCPClient):
        """
        Inicializa DocumentService.
        
        Args:
            gcp_client: Instância singleton de GCPClient
        """
        self.client = gcp_client
    
    def upload_file(
        self,
        corpus_id: str,
        file_path: str,
        display_name: str,
        description: str = None
    ) -> Any:
        """
        Faz upload de arquivo para RAG Corpus (até 25MB).
        
        Args:
            corpus_id: ID do corpus de destino
            file_path: Caminho local do arquivo
            display_name: Nome de exibição
            description: Descrição opcional
            
        Returns:
            RagFile object com detalhes do arquivo
            
        Note:
            O Vertex AI cuida automaticamente do upload para GCS.
            Limite de 25MB para upload direto.
        """
        corpus_name = self.client.build_corpus_name(corpus_id)
        
        response = rag.upload_file(
            corpus_name=corpus_name,
            path=file_path,
            display_name=display_name,
            description=description
        )
        
        return response
    
    def delete_file(self, corpus_id: str, file_id: str) -> None:
        """
        Deleta um arquivo (operação idempotente).
        
        Args:
            corpus_id: ID do corpus
            file_id: ID do arquivo a deletar
            
        Note:
            Operação idempotente - não gera erro se arquivo não existir.
        """
        file_name = self.client.build_file_name(corpus_id, file_id)
        
        try:
            rag.delete_file(name=file_name)
        except Exception:
            # Idempotente - ignorar erro se já deletado
            pass
    
    def get_file(self, corpus_id: str, file_id: str) -> Any:
        """
        Obtém detalhes de um arquivo específico.
        
        Args:
            corpus_id: ID do corpus
            file_id: ID do arquivo
            
        Returns:
            RagFile object com detalhes
        """
        file_name = self.client.build_file_name(corpus_id, file_id)
        return rag.get_file(name=file_name)
