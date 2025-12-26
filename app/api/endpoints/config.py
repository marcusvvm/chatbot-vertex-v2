"""
Configuration API endpoints.

Manages corpus-specific and global configurations.
Includes preset system for simplified configuration.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
from app.schemas.config import (
    CorpusConfigUpdate,
    CorpusConfigResponse,
    GlobalConfigResponse
)
from app.config.service import ConfigService
from app.config.models import CorpusChatConfig, GenerationConfig
from app.config.presets import get_preset_service, PresetService
from app.core.dependencies import verify_token, get_config_service
from app.schemas.auth import TokenData

router = APIRouter()


# ============================================================================
# PRESET ENDPOINTS
# ============================================================================

@router.get("/presets")
async def list_presets(
    token_data: TokenData = Depends(verify_token)
):
    """
    List all available presets (core + custom).
    
    Returns:
        List of preset summaries with id, name, description, model_name, is_core
    """
    preset_service = get_preset_service()
    presets = preset_service.list_presets()
    return {"presets": presets}


@router.get("/presets/{preset_id}")
async def get_preset(
    preset_id: str,
    token_data: TokenData = Depends(verify_token)
):
    """
    Get a specific preset by ID.
    
    Returns full preset configuration.
    """
    preset_service = get_preset_service()
    preset = preset_service.get_preset(preset_id)
    
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset not found: {preset_id}"
        )
    
    return preset


@router.post("/presets", status_code=status.HTTP_201_CREATED)
async def create_preset(
    preset_data: Dict[str, Any],
    token_data: TokenData = Depends(verify_token)
):
    """
    Create a new custom preset.
    
    Core presets cannot be created (reserved IDs: balanced, creative, precise, fast).
    
    Request body:
        - id: Unique preset identifier (required)
        - name: Display name
        - description: Preset description
        - model_name: Gemini model to use
        - generation_config: Generation parameters (passthrough)
        - rag_retrieval_top_k: Number of RAG documents
        - max_history_length: Max conversation history
    """
    preset_service = get_preset_service()
    
    try:
        preset = preset_service.create_preset(preset_data)
        return {"message": "Preset created successfully", "preset": preset}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/presets/{preset_id}")
async def update_preset(
    preset_id: str,
    preset_data: Dict[str, Any],
    token_data: TokenData = Depends(verify_token)
):
    """
    Update an existing custom preset.
    
    Core presets cannot be modified.
    """
    preset_service = get_preset_service()
    
    try:
        preset = preset_service.update_preset(preset_id, preset_data)
        return {"message": "Preset updated successfully", "preset": preset}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/presets/{preset_id}")
async def delete_preset(
    preset_id: str,
    token_data: TokenData = Depends(verify_token)
):
    """
    Delete a custom preset.
    
    Core presets cannot be deleted.
    """
    preset_service = get_preset_service()
    
    try:
        preset_service.delete_preset(preset_id)
        return {"message": f"Preset '{preset_id}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/corpus/{corpus_id}/apply-preset/{preset_id}")
async def apply_preset_to_corpus(
    corpus_id: str,
    preset_id: str,
    token_data: TokenData = Depends(verify_token),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Apply a preset to a corpus.
    
    This sets the corpus configuration to match the preset values.
    """
    preset_service = get_preset_service()
    preset = preset_service.get_preset(preset_id)
    
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset not found: {preset_id}"
        )
    
    # Build corpus config from preset
    config_data = {
        "corpus_id": corpus_id,
        "display_name": f"{corpus_id} - {preset['name']}",
        "model_name": preset.get("model_name"),
        "rag_retrieval_top_k": preset.get("rag_retrieval_top_k"),
        "max_history_length": preset.get("max_history_length")
    }
    
    # Add generation_config if present
    if preset.get("generation_config"):
        config_data["generation_config"] = GenerationConfig(
            **preset["generation_config"]
        )
    
    corpus_config = CorpusChatConfig(**config_data)
    config_service.save_corpus_config(corpus_id, corpus_config)
    
    return {
        "message": f"Preset '{preset['name']}' applied successfully",
        "corpus_id": corpus_id,
        "preset_id": preset_id
    }


# ============================================================================
# GLOBAL CONFIG ENDPOINTS
# ============================================================================

@router.get("/global", response_model=GlobalConfigResponse)
async def get_global_config(
    token_data: TokenData = Depends(verify_token),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get global configuration (read-only).
    
    Returns default values and system instruction.
    Fixed rules (formatting, safety) are not exposed.
    """
    global_config = config_service.load_global_config()
    
    return GlobalConfigResponse(
        system_instruction=global_config.system_instruction,
        defaults=global_config.defaults
    )


# ============================================================================
# CORPUS CONFIG ENDPOINTS
# ============================================================================

@router.get("/corpus/{corpus_id}", response_model=CorpusConfigResponse)
async def get_corpus_config(
    corpus_id: str,
    token_data: TokenData = Depends(verify_token),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get configuration for a specific corpus (customizable fields only).
    
    Returns the configuration that can be modified by users.
    Fixed/immutable fields (safety_settings, formatting_rules, etc.) are not exposed.
    """
    # Get user-visible config (excludes fixed/immutable fields)
    user_config = config_service.get_user_visible_config(corpus_id)
    
    # Check if has custom config
    corpus_config = config_service.load_corpus_config(corpus_id)
    has_custom = corpus_config is not None
    
    return CorpusConfigResponse(
        corpus_id=corpus_id,
        config=user_config,
        has_custom_config=has_custom
    )


@router.put("/corpus/{corpus_id}")
async def update_corpus_config(
    corpus_id: str,
    config_update: CorpusConfigUpdate,
    token_data: TokenData = Depends(verify_token),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Update configuration for a specific corpus.
    
    Creates or updates corpus-specific configuration.
    Only provided fields will be customized (others use global defaults).
    
    Uses passthrough for generation_config - validation delegated to Google API.
    """
    # Load existing config or create new
    existing_config = config_service.load_corpus_config(corpus_id)
    
    # Build corpus config
    config_data = {
        "corpus_id": corpus_id,
        "display_name": f"Corpus {corpus_id}"
    }
    
    # Add updated fields
    if config_update.system_instruction is not None:
        config_data["system_instruction"] = config_update.system_instruction
    elif existing_config and existing_config.system_instruction:
        config_data["system_instruction"] = existing_config.system_instruction
    
    if config_update.model_name is not None:
        config_data["model_name"] = config_update.model_name
    elif existing_config and existing_config.model_name:
        config_data["model_name"] = existing_config.model_name
    
    if config_update.generation_config is not None:
        # Passthrough: convert to dict and pass to GenerationConfig
        gen_dict = config_update.generation_config.model_dump(exclude_none=True)
        config_data["generation_config"] = GenerationConfig(**gen_dict)
    elif existing_config and existing_config.generation_config:
        config_data["generation_config"] = existing_config.generation_config
    
    if config_update.rag_retrieval_top_k is not None:
        config_data["rag_retrieval_top_k"] = config_update.rag_retrieval_top_k
    elif existing_config and existing_config.rag_retrieval_top_k:
        config_data["rag_retrieval_top_k"] = existing_config.rag_retrieval_top_k
    
    if config_update.timeout_seconds is not None:
        config_data["timeout_seconds"] = config_update.timeout_seconds
    elif existing_config and existing_config.timeout_seconds:
        config_data["timeout_seconds"] = existing_config.timeout_seconds
    
    if config_update.max_history_length is not None:
        config_data["max_history_length"] = config_update.max_history_length
    elif existing_config and existing_config.max_history_length:
        config_data["max_history_length"] = existing_config.max_history_length
    
    # Create and save config
    corpus_config = CorpusChatConfig(**config_data)
    config_service.save_corpus_config(corpus_id, corpus_config)
    
    return {
        "message": "Configuration updated successfully",
        "corpus_id": corpus_id
    }


@router.delete("/corpus/{corpus_id}")
async def delete_corpus_config(
    corpus_id: str,
    token_data: TokenData = Depends(verify_token),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Delete corpus-specific configuration.
    
    Resets corpus to use global defaults.
    """
    deleted = config_service.delete_corpus_config(corpus_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No custom configuration found for corpus {corpus_id}"
        )
    
    return {
        "message": "Configuration deleted successfully",
        "corpus_id": corpus_id
    }

