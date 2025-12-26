"""
Corpus Service - Gerencia operações de RAG Corpus.

Este módulo implementa a lógica de negócio para criar, listar,
deletar e gerenciar RAG Corpora (departamentos) no Vertex AI.

Single Responsibility: Apenas operações de Corpus.
"""

from vertexai.preview import rag
from typing import List, Any
from app.infrastructure.gcp.client import GCPClient


class CorpusService:
    """
    Service para gerenciar RAG Corpus (Departamentos).
    
    Responsabilidades:
    - Criar novos corpus com prefixo DEP-
    - Listar corpus do sistema
    - Deletar corpus (idempotente)
    - Listar arquivos de um corpus
    
    Dependencies:
    - GCPClient: Autenticação e helpers
    """
    
    def __init__(self, gcp_client: GCPClient):
        """
        Inicializa CorpusService.
        
        Args:
            gcp_client: Instância singleton de GCPClient
        """
        self.client = gcp_client
    
    def create_corpus(self, display_name: str, description: str = None) -> Any:
        """
        Cria novo RAG Corpus com prefixo DEP-.
        
        Args:
            display_name: Nome do departamento
            description: Descrição opcional
            
        Returns:
            RagCorpus object criado
            
        Note:
            Auto-adiciona prefixo 'DEP-' se ausente para isolamento do sistema.
        """
        # Enforce DEP- prefix para isolamento
        if not display_name.startswith("DEP-"):
            display_name = f"DEP-{display_name}"
        
        # Criar corpus (SDK handel LRO automaticamente)
        corpus = rag.create_corpus(
            display_name=display_name,
            description=description
        )
        return corpus
    
    def list_corpora(self) -> List[Any]:
        """
        Lista todos os corpus do sistema (apenas com prefixo DEP-).
        
        Returns:
            Lista de RagCorpus objects filtrados
            
        Note:
            Filtra apenas corpus que começam com 'DEP-' para isolar
            recursos do sistema de outros projetos no mesmo GCP project.
        """
        all_corpora = rag.list_corpora()
        
        # Filtrar apenas corpus do sistema
        system_corpora = [
            c for c in all_corpora
            if c.display_name.startswith("DEP-")
        ]
        
        return system_corpora
    
    def delete_corpus(self, corpus_id: str) -> None:
        """
        Deleta um corpus (operação idempotente).
        
        Args:
            corpus_id: ID do corpus a deletar
            
        Note:
            Operação idempotente - não gera erro se corpus não existir.
        """
        corpus_name = self.client.build_corpus_name(corpus_id)
        
        try:
            rag.delete_corpus(name=corpus_name)
        except Exception:
            # Idempotente - ignorar erro se já deletado
            pass
    
    def list_corpus_files(self, corpus_id: str) -> List[Any]:
        """
        Lista todos os arquivos de um corpus.
        
        Args:
            corpus_id: ID do corpus
            
        Returns:
            Lista de RagFile objects
        """
        corpus_name = self.client.build_corpus_name(corpus_id)
        files = rag.list_files(corpus_name=corpus_name)
        return list(files)
