"""
claude-tts: Multi-provider Text-to-Speech package for Claude Code integration.

Supports multiple TTS providers with automatic fallback and minimal configuration.
"""

from .loader import TTSLoader, load_tts
from .types import VoiceGender

__version__ = "0.1.0"
__all__ = ["TTSLoader", "load_tts", "VoiceGender"]