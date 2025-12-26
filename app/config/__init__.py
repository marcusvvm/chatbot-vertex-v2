"""
Configuration module for dynamic corpus management.

Handles loading, saving, and merging of corpus-specific configurations.
"""

from .service import ConfigService
from .models import (
    GenerationConfig,
    CorpusChatConfig,
    GlobalConfig
)

__all__ = [
    'ConfigService',
    'GenerationConfig',
    'CorpusChatConfig',
    'GlobalConfig'
]
