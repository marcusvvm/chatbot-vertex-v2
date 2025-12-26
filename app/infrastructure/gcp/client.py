"""
GCP Client - Singleton para gerenciar credenciais e clientes GCP.

Este módulo centraliza toda autenticação e inicialização de SDKs do Google Cloud,
garantindo que credenciais sejam carregadas apenas uma vez e compartilhadas entre
todos os services.
"""

import vertexai
from google import genai
from google.oauth2 import service_account
from app.core.config import settings


class GCPClient:
    """
    Singleton para gerenciar credenciais e clientes GCP.
    
    Responsabilidades:
    - Carregar credenciais GCP (service account)
    - Inicializar Vertex AI SDK (para RAG)
    - Inicializar GenAI Client (para Chat)
    - Prover helpers para construir resource names
    
    Design Pattern: Singleton via __new__
    """
    
    _instance = None
    
    def __new__(cls):
        """Garante que apenas uma instância existe (Singleton)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa credenciais e clientes (apenas uma vez)."""
        if self._initialized:
            return
        
        # Carregar credenciais do service account
        self.credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS
        ).with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
        
        # Inicializar Vertex AI (usado para RAG operations)
        vertexai.init(
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION,
            credentials=self.credentials
        )
        
        # Inicializar GenAI Client (usado para Chat operations)
        self.genai_client = genai.Client(
            vertexai=True,
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION_CHAT,
            credentials=self.credentials
        )
        
        self._initialized = True
    
    def build_corpus_name(self, corpus_id: str) -> str:
        """
        Constrói resource name completo de um RAG Corpus.
        
        Args:
            corpus_id: ID do corpus
            
        Returns:
            Resource name no formato:
            projects/{project}/locations/{location}/ragCorpora/{corpus_id}
        """
        return (
            f"projects/{settings.GCP_PROJECT_ID}/"
            f"locations/{settings.GCP_LOCATION}/"
            f"ragCorpora/{corpus_id}"
        )
    
    def build_file_name(self, corpus_id: str, file_id: str) -> str:
        """
        Constrói resource name completo de um RAG File.
        
        Args:
            corpus_id: ID do corpus
            file_id: ID do arquivo
            
        Returns:
            Resource name no formato:
            projects/{project}/locations/{location}/ragCorpora/{corpus_id}/ragFiles/{file_id}
        """
        corpus_name = self.build_corpus_name(corpus_id)
        return f"{corpus_name}/ragFiles/{file_id}"
