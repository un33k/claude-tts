"""Base TTS provider interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..types import VoiceGender


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""
    
    def __init__(self, voice_gender: VoiceGender = "female"):
        """Initialize the provider with voice preference."""
        self.voice_gender = voice_gender
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass
    
    @abstractmethod
    def speak(self, text: str) -> bool:
        """
        Speak the given text.
        
        Args:
            text: The text to speak
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}(name='{self.name}', available={self.is_available()})"