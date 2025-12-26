"""
Preset system for chat configuration.

Core presets are hardcoded (read-only).
Custom presets stored in config/presets.json (editable via API).
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


# Core presets (read-only, hardcoded)
CORE_PRESETS: Dict[str, Dict[str, Any]] = {
    "balanced": {
        "id": "balanced",
        "name": "Equilibrado (Recomendado)",
        "description": "Respostas precisas e rápidas. Bom para uso geral.",
        "is_core": True,
        "model_name": "gemini-2.5-pro",
        "generation_config": {
            "temperature": 0.2,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 4096,
            "thinking_budget": 1024
        },
        "rag_retrieval_top_k": 10,
        "max_history_length": 20
    },
    
    "creative": {
        "id": "creative",
        "name": "Criativo",
        "description": "Respostas mais elaboradas. Melhor para explicações complexas.",
        "is_core": True,
        "model_name": "gemini-2.5-pro",
        "generation_config": {
            "temperature": 0.5,
            "top_p": 0.95,
            "top_k": 60,
            "max_output_tokens": 8192,
            "thinking_budget": 2048
        },
        "rag_retrieval_top_k": 15,
        "max_history_length": 20
    },
    
    "precise": {
        "id": "precise",
        "name": "Preciso",
        "description": "Respostas concisas e factuais. Ideal para consultas rápidas.",
        "is_core": True,
        "model_name": "gemini-2.5-flash",
        "generation_config": {
            "temperature": 0.1,
            "top_p": 0.7,
            "top_k": 20,
            "max_output_tokens": 2048
        },
        "rag_retrieval_top_k": 5,
        "max_history_length": 20
    },
    
    "fast": {
        "id": "fast",
        "name": "Rápido",
        "description": "Otimizado para velocidade. Menor latência.",
        "is_core": True,
        "model_name": "gemini-2.5-flash",
        "generation_config": {
            "temperature": 0.2,
            "max_output_tokens": 1024
        },
        "rag_retrieval_top_k": 3,
        "max_history_length": 10
    }
}


class PresetService:
    """
    Service for managing chat configuration presets.
    
    Core presets are read-only (hardcoded).
    Custom presets can be created/edited/deleted via API.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize PresetService.
        
        Args:
            config_dir: Directory for config files (default: "config")
        """
        self.config_dir = Path(config_dir)
        self.custom_presets_file = self.config_dir / "presets.json"
        self._ensure_custom_presets_file()
    
    def _ensure_custom_presets_file(self) -> None:
        """Create empty presets.json if not exists."""
        if not self.custom_presets_file.exists():
            self.custom_presets_file.write_text("{}", encoding="utf-8")
    
    def _load_custom_presets(self) -> Dict[str, Dict[str, Any]]:
        """Load custom presets from file."""
        try:
            content = self.custom_presets_file.read_text(encoding="utf-8")
            return json.loads(content) if content.strip() else {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_custom_presets(self, presets: Dict[str, Dict[str, Any]]) -> None:
        """Save custom presets to file."""
        self.custom_presets_file.write_text(
            json.dumps(presets, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def get_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all presets (core + custom).
        
        Returns:
            Dict with all presets, keyed by preset ID
        """
        all_presets = CORE_PRESETS.copy()
        custom = self._load_custom_presets()
        
        # Mark custom presets
        for preset_id, preset in custom.items():
            preset["is_core"] = False
            all_presets[preset_id] = preset
        
        return all_presets
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """
        List all presets (summary format for API).
        
        Returns:
            List of preset summaries
        """
        all_presets = self.get_all_presets()
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "description": p["description"],
                "model_name": p["model_name"],
                "is_core": p.get("is_core", False)
            }
            for p in all_presets.values()
        ]
    
    def get_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific preset by ID.
        
        Args:
            preset_id: Preset identifier
            
        Returns:
            Preset dict or None if not found
        """
        all_presets = self.get_all_presets()
        return all_presets.get(preset_id)
    
    def create_preset(self, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new custom preset.
        
        Args:
            preset_data: Preset configuration
            
        Returns:
            Created preset
            
        Raises:
            ValueError: If preset ID already exists or is invalid
        """
        preset_id = preset_data.get("id")
        
        if not preset_id:
            raise ValueError("Preset ID is required")
        
        if preset_id in CORE_PRESETS:
            raise ValueError(f"Cannot create preset with core ID: {preset_id}")
        
        custom_presets = self._load_custom_presets()
        
        if preset_id in custom_presets:
            raise ValueError(f"Preset already exists: {preset_id}")
        
        # Ensure required fields
        preset = {
            "id": preset_id,
            "name": preset_data.get("name", preset_id),
            "description": preset_data.get("description", ""),
            "is_core": False,
            "model_name": preset_data.get("model_name", "gemini-2.5-pro"),
            "generation_config": preset_data.get("generation_config", {}),
            "rag_retrieval_top_k": preset_data.get("rag_retrieval_top_k", 10),
            "max_history_length": preset_data.get("max_history_length", 20)
        }
        
        custom_presets[preset_id] = preset
        self._save_custom_presets(custom_presets)
        
        return preset
    
    def update_preset(self, preset_id: str, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing custom preset.
        
        Args:
            preset_id: Preset to update
            preset_data: New configuration
            
        Returns:
            Updated preset
            
        Raises:
            ValueError: If preset is core or doesn't exist
        """
        if preset_id in CORE_PRESETS:
            raise ValueError(f"Cannot modify core preset: {preset_id}")
        
        custom_presets = self._load_custom_presets()
        
        if preset_id not in custom_presets:
            raise ValueError(f"Preset not found: {preset_id}")
        
        # Merge with existing
        existing = custom_presets[preset_id]
        updated = {
            "id": preset_id,
            "name": preset_data.get("name", existing.get("name", preset_id)),
            "description": preset_data.get("description", existing.get("description", "")),
            "is_core": False,
            "model_name": preset_data.get("model_name", existing.get("model_name")),
            "generation_config": preset_data.get("generation_config", existing.get("generation_config", {})),
            "rag_retrieval_top_k": preset_data.get("rag_retrieval_top_k", existing.get("rag_retrieval_top_k", 10)),
            "max_history_length": preset_data.get("max_history_length", existing.get("max_history_length", 20))
        }
        
        custom_presets[preset_id] = updated
        self._save_custom_presets(custom_presets)
        
        return updated
    
    def delete_preset(self, preset_id: str) -> bool:
        """
        Delete a custom preset.
        
        Args:
            preset_id: Preset to delete
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If preset is core or doesn't exist
        """
        if preset_id in CORE_PRESETS:
            raise ValueError(f"Cannot delete core preset: {preset_id}")
        
        custom_presets = self._load_custom_presets()
        
        if preset_id not in custom_presets:
            raise ValueError(f"Preset not found: {preset_id}")
        
        del custom_presets[preset_id]
        self._save_custom_presets(custom_presets)
        
        return True


# Singleton instance
_preset_service: Optional[PresetService] = None


def get_preset_service() -> PresetService:
    """Get or create PresetService singleton."""
    global _preset_service
    if _preset_service is None:
        _preset_service = PresetService()
    return _preset_service
