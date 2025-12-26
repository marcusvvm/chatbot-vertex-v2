"""
Chat service for RAG-based conversations.

Uses ConfigService for dynamic, per-corpus configuration.
Simplified architecture: no HistoryFilter (Gemini handles context).
"""

from google.genai import types
from typing import List, Dict
from app.infrastructure.gcp.client import GCPClient
from app.config.service import ConfigService
from app.config.adapters import GeminiConfigAdapter


class ChatService:
    """Service for chat operations with dynamic configuration."""
    
    def __init__(self, gcp_client: GCPClient, config_service: ConfigService):
        """
        Initialize ChatService with GCP client and config service.
        
        Args:
            gcp_client: GCP client for accessing Gemini API
            config_service: Service for loading corpus configurations
        """
        self.client = gcp_client
        self.config_service = config_service
        self.genai_client = gcp_client.genai_client
    
    def chat_rag(
        self,
        message: str,
        history: List[Dict],
        corpus_id: str
    ) -> str:
        """
        Execute chat with RAG grounding.
        
        Args:
            message: Current user message
            history: Conversation history (list of dicts with 'role' and 'content')
            corpus_id: Corpus ID for RAG grounding
            
        Returns:
            Model response (text)
            
        Note:
            - Loads configuration dynamically from ConfigService per corpus
            - Uses simple history slicing (Gemini handles context intelligently)
            - Preserves client's rag_config (rag_retrieval_top_k)
            - Applies safety_settings from fixed config
        """
        # 1. Load dynamic configuration for this corpus
        config = self.config_service.get_merged_config(corpus_id)
        
        # 2. Simple history filtering: keep last N messages
        # Context management delegated to Gemini via system prompt
        max_history = config.get('max_history_length', 20)
        filtered_history = history[-max_history:] if history else []
        
        # 3. Build RAG tool (with client's config)
        corpus_name = self.client.build_corpus_name(corpus_id)
        rag_tool = types.Tool(
            retrieval=types.Retrieval(
                vertex_rag_store=types.VertexRagStore(
                    rag_corpora=[corpus_name],
                    similarity_top_k=config.get('rag_retrieval_top_k', 10)
                )
            )
        )
        
        # 4. Convert filtered history to google.genai format
        contents = []
        
        for msg in filtered_history:
            role = "user" if msg['role'] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=msg['content'])]
            ))
        
        # 5. Add current message with SANDWICH PROMPTING
        # Critical reminder injected BEFORE user message to mitigate "Lost in the Middle"
        # effect where system instructions get ignored in long conversations
        critical_reminder = config.get(
            'critical_reminder',
            "Lembre-se: Se esta solicitação for ambígua, peça clarificação ANTES de responder. "
            "Você controla o fluxo da conversa."
        )
        
        # Inject reminder as part of the user message context
        enhanced_message = f"[LEMBRETE: {critical_reminder}]\n\n{message}"
        
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=enhanced_message)]
        ))
        
        # 6. Build GenerateContentConfig using adapter (DRY, centralized)
        # Adapter handles all parameter translation, safety_settings, thinking_budget
        generate_config = GeminiConfigAdapter.build_generate_content_config(
            merged_config=config,
            tools=[rag_tool]
        )
        
        # 7. Generate response with dynamic model
        model_name = config.get('model_name', 'gemini-2.5-pro')
        response = self.genai_client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_config
        )
        
        return response.text
