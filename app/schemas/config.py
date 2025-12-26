"""
Schemas for configuration API endpoints.

Defines request/response models for configuration management.
Supports passthrough parameters for future Gemini API compatibility.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class GenerationConfigUpdate(BaseModel):
    """
    Generation config for API updates.
    
    Uses passthrough: accepts any valid Gemini API parameter.
    Validation delegated to Google API at runtime.
    """
    model_config = ConfigDict(extra="allow")  # Allow unknown fields
    
    # Common fields (documented, but not strictly validated)
    temperature: Optional[float] = Field(None, description="Creativity (0.0-2.0)")
    top_p: Optional[float] = Field(None, description="Nucleus sampling (0.0-1.0)")
    top_k: Optional[int] = Field(None, description="Top-K sampling")
    max_output_tokens: Optional[int] = Field(None, description="Max tokens in response")
    
    # Thinking params (model-dependent)
    thinking_budget: Optional[int] = Field(None, description="Gemini 2.5: thinking tokens")
    thinking_level: Optional[str] = Field(None, description="Gemini 3: low/medium/high")


class CorpusConfigUpdate(BaseModel):
    """Request body for updating corpus configuration."""
    system_instruction: Optional[str] = Field(None, max_length=10000)
    model_name: Optional[str] = None
    generation_config: Optional[GenerationConfigUpdate] = None
    rag_retrieval_top_k: Optional[int] = Field(None, ge=1, le=50)
    timeout_seconds: Optional[float] = Field(None, ge=10.0, le=300.0)
    max_history_length: Optional[int] = Field(None, ge=1, le=100)


class CorpusConfigResponse(BaseModel):
    """Response with full corpus configuration (merged)."""
    corpus_id: str
    config: Dict[str, Any] = Field(..., description="Merged configuration (global + corpus)")
    has_custom_config: bool = Field(..., description="Whether corpus has custom config")


class GlobalConfigResponse(BaseModel):
    """Response with global configuration (read-only, excludes fixed rules)."""
    system_instruction: str
    defaults: Dict[str, Any]
