"""ElevenLabs TTS provider."""

import logging
import os
from typing import Optional

from .base import TTSProvider
from ..types import VoiceGender

logger = logging.getLogger(__name__)


class ElevenLabsProvider(TTSProvider):
    """TTS provider using ElevenLabs API."""
    
    # Default voice IDs for each gender
    DEFAULT_VOICES = {
        "male": "pNInz6obpgDQGcFmaJgB",  # Adam
        "female": "21m00Tcm4TlvDq8ikWAM"  # Rachel
    }
    
    def __init__(self, voice_gender: VoiceGender = "female"):
        """Initialize the ElevenLabs provider."""
        super().__init__(voice_gender)
        self._client: Optional[object] = None
        self._voice_id = self._get_voice_id()
        self._api_key = os.getenv("ELEVENLABS_API_KEY")
        self._available = self._check_availability()
    
    @property
    def name(self) -> str:
        """Return the provider name."""
        return "elevenlabs"
    
    def _get_voice_id(self) -> str:
        """Get the voice ID from environment or use default."""
        env_voice = os.getenv("TTS_ELEVENLABS_VOICE_ID")
        if env_voice:
            return env_voice
        return self.DEFAULT_VOICES.get(self.voice_gender, self.DEFAULT_VOICES["female"])
    
    def _check_availability(self) -> bool:
        """Check if ElevenLabs is available."""
        if not self._api_key:
            logger.debug("ElevenLabs API key not found")
            return False
        
        try:
            from elevenlabs import VoiceSettings
            return True
        except ImportError:
            logger.debug("elevenlabs package not installed")
            return False
        except Exception as e:
            logger.debug(f"ElevenLabs not available: {e}")
            return False
    
    def _get_client(self) -> Optional[object]:
        """Get or create the ElevenLabs client."""
        if self._client is None:
            try:
                from elevenlabs import ElevenLabs
                self._client = ElevenLabs(api_key=self._api_key)
            except Exception as e:
                logger.error(f"Failed to initialize ElevenLabs client: {e}")
                return None
        return self._client
    
    def is_available(self) -> bool:
        """Check if the provider is available."""
        return self._available
    
    def speak(self, text: str) -> bool:
        """
        Speak the given text using ElevenLabs.
        
        Args:
            text: The text to speak
            
        Returns:
            True if successful, False otherwise
        """
        client = self._get_client()
        if not client:
            return False
        
        try:
            from elevenlabs import play, VoiceSettings
            
            # Generate audio
            audio = client.generate(
                text=text,
                voice=self._voice_id,
                model="eleven_monolingual_v1",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.5
                )
            )
            
            # Play the audio
            play(audio)
            return True
            
        except Exception as e:
            logger.error(f"ElevenLabs speak failed: {e}")
            return False