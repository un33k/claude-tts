"""Type definitions for claude-tts."""

from typing import Literal, TypedDict, Optional

VoiceGender = Literal["male", "female"]

class ProviderConfig(TypedDict, total=False):
    """Configuration for a TTS provider."""
    api_key: Optional[str]
    voice_id: Optional[str]
    model: Optional[str]
    voice_gender: Optional[VoiceGender]