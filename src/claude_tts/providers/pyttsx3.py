"""Pyttsx3 TTS provider for offline text-to-speech."""

import logging
from typing import Optional

from .base import TTSProvider
from ..types import VoiceGender

logger = logging.getLogger(__name__)


class Pyttsx3Provider(TTSProvider):
    """Offline TTS provider using pyttsx3."""
    
    def __init__(self, voice_gender: VoiceGender = "female"):
        """Initialize the pyttsx3 provider."""
        super().__init__(voice_gender)
        self._engine: Optional[object] = None
        self._available = self._check_availability()
    
    @property
    def name(self) -> str:
        """Return the provider name."""
        return "pyttsx3"
    
    def _check_availability(self) -> bool:
        """Check if pyttsx3 is available."""
        try:
            import pyttsx3
            # Try to create an engine to verify it works
            engine = pyttsx3.init()
            engine.stop()
            return True
        except Exception as e:
            logger.debug(f"pyttsx3 not available: {e}")
            return False
    
    def _get_engine(self) -> Optional[object]:
        """Get or create the pyttsx3 engine."""
        if self._engine is None:
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._configure_voice()
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3: {e}")
                return None
        return self._engine
    
    def _configure_voice(self) -> None:
        """Configure the voice based on gender preference."""
        if not self._engine:
            return
        
        try:
            voices = self._engine.getProperty('voices')
            if not voices:
                return
            
            # Try to find a voice matching the gender preference
            for voice in voices:
                voice_name = voice.name.lower()
                if self.voice_gender == "female" and any(
                    word in voice_name for word in ["female", "woman", "girl", "zira", "hazel"]
                ):
                    self._engine.setProperty('voice', voice.id)
                    break
                elif self.voice_gender == "male" and any(
                    word in voice_name for word in ["male", "man", "boy", "david", "george"]
                ):
                    self._engine.setProperty('voice', voice.id)
                    break
            
            # Set reasonable speech rate
            self._engine.setProperty('rate', 150)
            
        except Exception as e:
            logger.debug(f"Could not configure voice: {e}")
    
    def is_available(self) -> bool:
        """Check if the provider is available."""
        return self._available
    
    def speak(self, text: str) -> bool:
        """
        Speak the given text using pyttsx3.
        
        Args:
            text: The text to speak
            
        Returns:
            True if successful, False otherwise
        """
        engine = self._get_engine()
        if not engine:
            return False
        
        try:
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"pyttsx3 speak failed: {e}")
            # Reset engine on failure
            self._engine = None
            return False