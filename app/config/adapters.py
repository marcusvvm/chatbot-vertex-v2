"""
Adapter layer for Google Gemini SDK.

Simplified passthrough design:
- Generation config params passed directly to Google SDK
- Validation delegated to Google API (future-proof)
- Only safety_settings need translation (category names)
"""

from typing import Dict, Any, List
from google.genai import types


class GeminiConfigAdapter:
    """
    Adapter for translating configuration to Google Gemini SDK format.
    
    Design: Passthrough with minimal translation.
    Only safety_settings require mapping (category names).
    """
    
    @classmethod
    def build_generate_content_config(
        cls,
        merged_config: Dict[str, Any],
        tools: List[types.Tool]
    ) -> types.GenerateContentConfig:
        """
        Build complete GenerateContentConfig from merged configuration.
        
        Uses passthrough for generation params - Google API validates.
        
        Args:
            merged_config: Merged configuration (fixed + global + corpus)
            tools: List of tools (RAG, Search, etc.)
        
        Returns:
            GenerateContentConfig ready for use with Gemini SDK
        """
        # 1. Get generation_config (passthrough)
        gen_config = merged_config.get('generation_config', {})
        
        # 2. Handle thinking_config separately (it's a nested object)
        thinking_config = None
        thinking_budget = gen_config.pop('thinking_budget', None) if isinstance(gen_config, dict) else None
        thinking_level = gen_config.pop('thinking_level', None) if isinstance(gen_config, dict) else None
        
        # Fallback to top-level thinking_budget if not in generation_config
        if thinking_budget is None:
            thinking_budget = merged_config.get('thinking_budget')
        
        if thinking_budget is not None:
            thinking_config = types.ThinkingConfig(thinking_budget=thinking_budget)
        elif thinking_level is not None:
            # Gemini 3 uses thinking_level (string)
            thinking_config = types.ThinkingConfig(thinking_level=thinking_level)
        
        # 3. Build GenerateContentConfig with passthrough
        generate_config = types.GenerateContentConfig(
            system_instruction=merged_config.get('system_instruction'),
            tools=tools,
            **gen_config  # PASSTHROUGH: all params go directly to SDK
        )
        
        # 4. Add thinking_config if present
        if thinking_config:
            generate_config.thinking_config = thinking_config
        
        # 5. Add safety_settings if available (needs translation)
        if 'safety_settings' in merged_config:
            generate_config.safety_settings = cls._build_safety_settings(
                merged_config['safety_settings']
            )
        
        return generate_config
    
    @classmethod
    def _build_safety_settings(cls, safety_dict: Dict[str, str]) -> List[types.SafetySetting]:
        """
        Convert safety_settings dict to Google SDK format.
        
        Args:
            safety_dict: Dict with categories and thresholds
                        (ex: {"harassment": "BLOCK_MEDIUM_AND_ABOVE"})
        
        Returns:
            List of SafetySetting objects for SDK
        """
        # Mapping of our keys to SDK category names
        category_mapping = {
            "harassment": "HARM_CATEGORY_HARASSMENT",
            "hate_speech": "HARM_CATEGORY_HATE_SPEECH",
            "sexually_explicit": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "dangerous_content": "HARM_CATEGORY_DANGEROUS_CONTENT"
        }
        
        settings = []
        for key, threshold in safety_dict.items():
            if key in category_mapping:
                settings.append(types.SafetySetting(
                    category=category_mapping[key],
                    threshold=threshold
                ))
        
        return settings
