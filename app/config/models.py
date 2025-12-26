"""
Pydantic models for configuration validation.

Defines schemas for:
- GenerationConfig: LLM generation parameters (passthrough)
- CorpusChatConfig: Corpus-specific chat configuration
- GlobalConfig: Global default configuration
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class GenerationConfig(BaseModel):
    """
    Configuration for LLM generation parameters.
    
    Uses passthrough: accepts any valid Gemini API parameter.
    Validation delegated to Google API at runtime.
    This enables future-proofing for new Gemini models.
    """
    
    # Common generation parameters (documented, not strictly validated)
    temperature: Optional[float] = Field(
        None,
        description="Controls randomness (0=deterministic, 2=very random)"
    )
    top_p: Optional[float] = Field(
        None,
        description="Nucleus sampling threshold"
    )
    top_k: Optional[int] = Field(
        None,
        description="Top-K sampling parameter"
    )
    max_output_tokens: Optional[int] = Field(
        None,
        description="Maximum tokens in response"
    )
    
    # Thinking params (model-dependent, passthrough)
    thinking_budget: Optional[int] = Field(
        None,
        description="Gemini 2.5: tokens for internal reasoning"
    )
    thinking_level: Optional[str] = Field(
        None,
        description="Gemini 3: thinking level (low/medium/high)"
    )
    
    model_config = ConfigDict(
        extra="allow",  # PASSTHROUGH: accept unknown fields
        str_max_length=1000
    )


class CorpusChatConfig(BaseModel):
    """
    Corpus-specific chat configuration.
    
    Overrides global defaults for a specific corpus/department.
    Lazy creation: only exists if customized.
    """
    
    corpus_id: str = Field(..., description="Vertex AI corpus ID")
    display_name: str = Field(..., description="Human-readable corpus name")
    
    # Chat persona and model
    system_instruction: Optional[str] = Field(
        None,
        max_length=10000,
        description="Custom system instruction (persona). Overrides global template."
    )
    model_name: Optional[str] = Field(
        None,
        description="LLM model to use (e.g., gemini-2.5-pro, gemini-1.5-flash)"
    )
    
    # Generation parameters
    generation_config: Optional[GenerationConfig] = Field(
        None,
        description="Generation parameters (temperature, top_k, etc.)"
    )
    
    # RAG configuration
    rag_retrieval_top_k: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Number of document chunks to retrieve for RAG"
    )
    
    # Performance tuning
    timeout_seconds: Optional[float] = Field(
        None,
        ge=10.0,
        le=300.0,
        description="Request timeout in seconds"
    )
    thinking_budget: Optional[int] = Field(
        None,
        ge=128,
        le=4096,
        description="Thinking budget for gemini-2.5-pro (tokens for internal reasoning)"
    )
    max_history_length: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Maximum conversation history length"
    )
    
    model_config = ConfigDict(extra="forbid")


class FixedConfig(BaseModel):
    """
    Fixed configuration that cannot be overridden by clients.
    
    Loaded from config/fixed.json.
    Contains security, formatting rules, and tools configuration that are immutable.
    """
    
    formatting_rules: str = Field(
        ..., 
        description="Markdown formatting rules (immutable)"
    )
    safety_settings: Dict[str, Any] = Field(
        ..., 
        description="Safety thresholds (immutable)"
    )
    tool_usage_instructions: Optional[str] = Field(
        None,
        description="Instructions for intelligent tool usage"
    )
    context_management_instructions: Optional[str] = Field(
        None,
        description="Instructions for context/history management"
    )
    critical_reminder: Optional[str] = Field(
        None,
        description="Critical reminder for sandwich prompting (injected before user message)"
    )
    
    model_config = ConfigDict(extra="forbid")


class GlobalConfig(BaseModel):
    """
    Global configuration defaults.
    
    Loaded from config/global.json.
    Provides base values for all corpus configs.
    """
    
    # System instruction (complete, includes persona and grounding rules)
    system_instruction: str = Field(
        ..., 
        description="Complete system instruction with persona and grounding rules"
    )
    
    # Default values (customizable per corpus)
    defaults: Dict[str, Any] = Field(
        ...,
        description="Default values for model_name, generation_config, etc."
    )
    
    model_config = ConfigDict(extra="allow")
