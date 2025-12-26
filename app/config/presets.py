"""
Preset system for chat configuration.

All presets are stored in config/presets.json and are fully editable via API.
Default presets (balanced, creative, precise, fast) are seeded on first startup.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path


# Default presets (seeded if presets.json is empty)
DEFAULT_PRESETS: Dict[str, Dict[str, Any]] = {
    "balanced": {
        "id": "balanced",
        "name": "Equilibrado (Recomendado)",
        "description": "Respostas precisas e rápidas. Bom para uso geral.",
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
    
    All presets are stored in config/presets.json and can be created,
    updated, or deleted via API. Default presets are seeded on first startup.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize PresetService.
        
        Args:
            config_dir: Directory for config files (default: "config")
        """
        self.config_dir = Path(config_dir)
        self.presets_file = self.config_dir / "presets.json"
        self._ensure_presets_file()
        self._seed_defaults_if_empty()
    
    def _ensure_presets_file(self) -> None:
        """Create empty presets.json if not exists."""
        if not self.presets_file.exists():
            self.presets_file.write_text("{}", encoding="utf-8")
    
    def _seed_defaults_if_empty(self) -> None:
        """Seed default presets if file is empty."""
        presets = self._load_presets()
        if not presets:
            for preset_id, preset_data in DEFAULT_PRESETS.items():
                presets[preset_id] = preset_data
            self._save_presets(presets)
    
    def _load_presets(self) -> Dict[str, Dict[str, Any]]:
        """Load presets from file."""
        try:
            content = self.presets_file.read_text(encoding="utf-8")
            return json.loads(content) if content.strip() else {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_presets(self, presets: Dict[str, Dict[str, Any]]) -> None:
        """Save presets to file."""
        self.presets_file.write_text(
            json.dumps(presets, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def get_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all presets.
        
        Returns:
            Dict with all presets, keyed by preset ID
        """
        return self._load_presets()
    
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
                "model_name": p["model_name"]
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
        Create a new preset.
        
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
            
        if len(preset_id) > 64:
            raise ValueError("Preset ID exceeds 64 characters")
        
        presets = self._load_presets()
        
        if preset_id in presets:
            raise ValueError(f"Preset already exists: {preset_id}")
        
        # Build preset with required fields
        preset = {
            "id": preset_id,
            "name": preset_data.get("name", preset_id),
            "description": preset_data.get("description", ""),
            "model_name": preset_data.get("model_name", "gemini-2.5-pro"),
            "generation_config": preset_data.get("generation_config", {}),
            "rag_retrieval_top_k": preset_data.get("rag_retrieval_top_k", 10),
            "max_history_length": preset_data.get("max_history_length", 20)
        }
        
        presets[preset_id] = preset
        self._save_presets(presets)
        
        return preset
    
    def update_preset(self, preset_id: str, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing preset.
        
        Args:
            preset_id: Preset to update
            preset_data: New configuration
            
        Returns:
            Updated preset
            
        Raises:
            ValueError: If preset doesn't exist
        """
        presets = self._load_presets()
        
        if preset_id not in presets:
            raise ValueError(f"Preset not found: {preset_id}")
        
        # Merge with existing
        existing = presets[preset_id]
        updated = {
            "id": preset_id,
            "name": preset_data.get("name", existing.get("name", preset_id)),
            "description": preset_data.get("description", existing.get("description", "")),
            "model_name": preset_data.get("model_name", existing.get("model_name")),
            "generation_config": preset_data.get("generation_config", existing.get("generation_config", {})),
            "rag_retrieval_top_k": preset_data.get("rag_retrieval_top_k", existing.get("rag_retrieval_top_k", 10)),
            "max_history_length": preset_data.get("max_history_length", existing.get("max_history_length", 20))
        }
        
        presets[preset_id] = updated
        self._save_presets(presets)
        
        return updated
    
    def delete_preset(self, preset_id: str) -> bool:
        """
        Delete a preset.
        
        Args:
            preset_id: Preset to delete
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If preset doesn't exist
        """
        presets = self._load_presets()
        
        if preset_id not in presets:
            raise ValueError(f"Preset not found: {preset_id}")
        
        del presets[preset_id]
        self._save_presets(presets)
        
        return True


# Singleton instance
_preset_service: Optional[PresetService] = None


def get_preset_service() -> PresetService:
    """Get or create PresetService singleton."""
    global _preset_service
    if _preset_service is None:
        _preset_service = PresetService()
    return _preset_service
