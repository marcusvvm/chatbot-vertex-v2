from pydantic import BaseModel, field_validator
from typing import List, Optional

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    corpus_id: str
    
    # History validation removed - now handled by ConfigService
    # max_history_length is per-corpus configuration

class ChatResponse(BaseModel):
    response: str
    new_history: List[Message]
