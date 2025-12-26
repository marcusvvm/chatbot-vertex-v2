"""
Configuration service for managing corpus-specific configurations.

Responsibilities (SRP):
- Load global configuration from JSON
- Load corpus-specific configuration from JSON
- Save corpus configuration
- Merge global + corpus configs
- Delete corpus configuration
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .models import CorpusChatConfig, GlobalConfig, GenerationConfig, FixedConfig


class ConfigService:
    """
    Service for managing configuration files.
    
    Storage: JSON files in config/
    - config/fixed.json: Immutable rules (formatting, safety)
    - config/global.json: Global defaults (customizable)
    - config/corpus/{corpus_id}.json: Corpus-specific overrides
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize ConfigService.
        
        Args:
            config_dir: Root directory for configuration files
        """
        self.config_dir = Path(config_dir)
        self.fixed_config_path = self.config_dir / "fixed.json"
        self.global_config_path = self.config_dir / "global.json"
        self.corpus_config_dir = self.config_dir / "corpus"
        
        # Ensure directories exist
        self.corpus_config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_fixed_config(self) -> FixedConfig:
        """
        Load fixed configuration from config/fixed.json.
        
        Returns:
            FixedConfig with immutable rules (formatting, safety)
            
        Raises:
            FileNotFoundError: If fixed.json doesn't exist
            ValueError: If JSON is invalid
        """
        if not self.fixed_config_path.exists():
            raise FileNotFoundError(
                f"Fixed configuration not found: {self.fixed_config_path}"
            )
        
        with open(self.fixed_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return FixedConfig(**data)
    
    def load_global_config(self) -> GlobalConfig:
        """
        Load global configuration from config/global.json.
        
        Returns:
            GlobalConfig with defaults and customizable rules
            
        Raises:
            FileNotFoundError: If global.json doesn't exist
            ValueError: If JSON is invalid
        """
        if not self.global_config_path.exists():
            raise FileNotFoundError(
                f"Global configuration not found: {self.global_config_path}"
            )
        
        with open(self.global_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return GlobalConfig(**data)
    
    def load_corpus_config(self, corpus_id: str) -> Optional[CorpusChatConfig]:
        """
        Load corpus-specific configuration.
        
        Args:
            corpus_id: Vertex AI corpus ID
            
        Returns:
            CorpusChatConfig if exists, None otherwise
        """
        corpus_config_path = self.corpus_config_dir / f"{corpus_id}.json"
        
        if not corpus_config_path.exists():
            return None
        
        with open(corpus_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return CorpusChatConfig(**data)
    
    def save_corpus_config(self, corpus_id: str, config: CorpusChatConfig) -> None:
        """
        Save corpus-specific configuration.
        
        Args:
            corpus_id: Vertex AI corpus ID
            config: CorpusChatConfig to save
        """
        corpus_config_path = self.corpus_config_dir / f"{corpus_id}.json"
        
        # Convert Pydantic model to dict (excludes None values)
        config_dict = config.model_dump(exclude_none=True, mode='json')
        
        with open(corpus_config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    def delete_corpus_config(self, corpus_id: str) -> bool:
        """
        Delete corpus-specific configuration.
        
        Args:
            corpus_id: Vertex AI corpus ID
            
        Returns:
            True if file was deleted, False if it didn't exist
        """
        corpus_config_path = self.corpus_config_dir / f"{corpus_id}.json"
        
        if corpus_config_path.exists():
            corpus_config_path.unlink()
            return True
        
        return False
    
    def get_merged_config(self, corpus_id: str) -> Dict[str, Any]:
        """
        Get final configuration for a corpus (fixed + global + corpus overrides).
        
        Merge strategy:
        1. Start with global defaults
        2. Override with corpus-specific values (if they exist)
        3. Build system_instruction (corpus or global + formatting_rules)
        4. Apply safety_settings from fixed (never overridable)
        
        Args:
            corpus_id: Vertex AI corpus ID
            
        Returns:
            Dict with merged configuration ready for ChatService
        """
        # Load configs
        fixed_config = self.load_fixed_config()
        global_config = self.load_global_config()
        
        # Start with global defaults
        merged = global_config.defaults.copy()
        
        # Load corpus-specific config (if exists)
        corpus_config = self.load_corpus_config(corpus_id)
        
        if corpus_config:
            # Override with corpus-specific values
            if corpus_config.model_name is not None:
                merged['model_name'] = corpus_config.model_name
            
            if corpus_config.generation_config is not None:
                # Merge generation_config
                gen_config_dict = corpus_config.generation_config.model_dump(exclude_none=True)
                if 'generation_config' in merged:
                    merged['generation_config'].update(gen_config_dict)
                else:
                    merged['generation_config'] = gen_config_dict
            
            if corpus_config.rag_retrieval_top_k is not None:
                merged['rag_retrieval_top_k'] = corpus_config.rag_retrieval_top_k
            
            if corpus_config.timeout_seconds is not None:
                merged['timeout_seconds'] = corpus_config.timeout_seconds
            
            if corpus_config.thinking_budget is not None:
                merged['thinking_budget'] = corpus_config.thinking_budget
            
            if corpus_config.max_history_length is not None:
                merged['max_history_length'] = corpus_config.max_history_length
        
        # Build system_instruction COMPLETE (base + formatting + tool instructions)
        # If corpus has custom instruction, use it; otherwise use global
        if corpus_config and corpus_config.system_instruction:
            base_instruction = corpus_config.system_instruction
        else:
            base_instruction = global_config.system_instruction
        
        # Concatenate formatting_rules (always from fixed.json)
        merged['system_instruction'] = (
            base_instruction + 
            "\n\n" + 
            fixed_config.formatting_rules
        )
        
        # Concatenate tool_usage_instructions if available (from fixed.json)
        if fixed_config.tool_usage_instructions:
            merged['system_instruction'] += "\n\n" + fixed_config.tool_usage_instructions
        
        # Concatenate context_management_instructions if available (from fixed.json)
        if fixed_config.context_management_instructions:
            merged['system_instruction'] += "\n\n" + fixed_config.context_management_instructions
        
        # Add safety_settings (from fixed.json, NEVER overridable, used directly by SDK)
        merged['safety_settings'] = fixed_config.safety_settings
        
        # Add critical_reminder for sandwich prompting (from fixed.json)
        if fixed_config.critical_reminder:
            merged['critical_reminder'] = fixed_config.critical_reminder
        
        return merged
    
    def get_user_visible_config(self, corpus_id: str) -> Dict[str, Any]:
        """
        Get configuration visible to users (excludes fixed/immutable fields).
        
        Returns ONLY customizable fields in their RAW form (without fixed merging).
        This means system_instruction contains ONLY the base instruction,
        NOT the concatenated version with formatting_rules + tool_usage_instructions.
        
        Removes fields that cannot be customized by users:
        - safety_settings (security, immutable)
        - formatting_rules (UX consistency, immutable)
        - tool_usage_instructions (system behavior, immutable)
        - tools_configuration (system behavior, immutable)
        
        Args:
            corpus_id: Vertex AI corpus ID
        
        Returns:
            Dict with only customizable configuration fields (RAW, not merged)
        
        Note:
            Use this method for API responses to avoid exposing
            immutable configs that users cannot modify.
            
            The system_instruction returned is the BASE instruction only,
            not the merged version used internally by ChatService.
        """
        # Load corpus and global configs
        corpus_config = self.load_corpus_config(corpus_id)
        global_config = self.load_global_config()
        
        # Start with global defaults
        merged = global_config.defaults.copy()
        
        # Override with corpus-specific values if they exist
        if corpus_config:
            if corpus_config.model_name:
                merged['model_name'] = corpus_config.model_name
            
            if corpus_config.generation_config:
                # Merge generation_config dicts
                base_gen_config = merged.get('generation_config', {})
                corpus_gen_config = corpus_config.generation_config.model_dump(exclude_none=True)
                merged['generation_config'] = {**base_gen_config, **corpus_gen_config}
            
            if corpus_config.rag_retrieval_top_k is not None:
                merged['rag_retrieval_top_k'] = corpus_config.rag_retrieval_top_k
                
            if corpus_config.timeout_seconds is not None:
                merged['timeout_seconds'] = corpus_config.timeout_seconds
                
            if corpus_config.thinking_budget is not None:
                merged['thinking_budget'] = corpus_config.thinking_budget
                
            if corpus_config.max_history_length is not None:
                merged['max_history_length'] = corpus_config.max_history_length
        
        # Build BASE system_instruction (NO fixed concatenation)
        # Return only the customizable part
        if corpus_config and corpus_config.system_instruction:
            merged['system_instruction'] = corpus_config.system_instruction
        else:
            merged['system_instruction'] = global_config.system_instruction
        
        # NOTE: We do NOT add formatting_rules or tool_usage_instructions here
        # Those are INTERNAL implementation details merged only in get_merged_config()
        # for use by ChatService. They should NEVER be exposed to API clients.
        
        return merged
