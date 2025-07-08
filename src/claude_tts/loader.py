"""TTS loader with automatic provider fallback."""

import os
from typing import Dict, List, Optional, Type

from .providers.base import TTSProvider
from .types import VoiceGender


class TTSLoader:
    """Manages TTS providers with automatic fallback."""
    
    def __init__(
        self,
        priority: Optional[List[str]] = None,
        voice_gender: VoiceGender = "female"
    ):
        """
        Initialize the TTS loader.
        
        Args:
            priority: List of provider names in order of preference
            voice_gender: Preferred voice gender (male/female)
        """
        self.voice_gender = voice_gender
        self.providers: Dict[str, TTSProvider] = {}
        self._priority = priority or self._get_default_priority()
        
        # Lazy load providers
        self._load_providers()
    
    def _get_default_priority(self) -> List[str]:
        """Get default provider priority from environment or fallback."""
        env_priority = os.getenv("TTS_PRIORITY")
        if env_priority:
            return [p.strip() for p in env_priority.split(",")]
        return ["pyttsx3", "elevenlabs", "openai", "gemini"]
    
    def _load_providers(self) -> None:
        """Lazy load available providers."""
        provider_classes: Dict[str, Type[TTSProvider]] = {}
        
        # Try to import each provider
        try:
            from .providers.pyttsx3 import Pyttsx3Provider
            provider_classes["pyttsx3"] = Pyttsx3Provider
        except ImportError:
            pass
        
        try:
            from .providers.elevenlabs import ElevenLabsProvider
            provider_classes["elevenlabs"] = ElevenLabsProvider
        except ImportError:
            pass
        
        try:
            from .providers.openai import OpenAIProvider
            provider_classes["openai"] = OpenAIProvider
        except ImportError:
            pass
        
        try:
            from .providers.gemini import GeminiProvider
            provider_classes["gemini"] = GeminiProvider
        except ImportError:
            pass
        
        # Instantiate providers
        for name, provider_class in provider_classes.items():
            try:
                self.providers[name] = provider_class(voice_gender=self.voice_gender)
            except Exception:
                # Provider initialization failed, skip it
                pass
    
    def get_provider(self, name: Optional[str] = None) -> Optional[TTSProvider]:
        """
        Get a specific provider or the first available one.
        
        Args:
            name: Optional provider name to get
            
        Returns:
            The requested provider or None if not available
        """
        if name:
            provider = self.providers.get(name)
            if provider and provider.is_available():
                return provider
            return None
        
        # Get first available provider based on priority
        for provider_name in self._priority:
            provider = self.providers.get(provider_name)
            if provider and provider.is_available():
                return provider
        
        return None
    
    def list_available(self) -> List[str]:
        """List all available provider names."""
        return [
            name for name, provider in self.providers.items()
            if provider.is_available()
        ]
    
    def speak(self, text: str, provider_name: Optional[str] = None) -> bool:
        """
        Speak text using the specified or best available provider.
        
        Args:
            text: The text to speak
            provider_name: Optional specific provider to use
            
        Returns:
            True if successful, False if no provider could speak
        """
        if provider_name:
            # Try specific provider
            provider = self.get_provider(provider_name)
            if provider:
                return provider.speak(text)
            return False
        
        # Try providers in priority order
        for name in self._priority:
            provider = self.providers.get(name)
            if provider and provider.is_available():
                try:
                    if provider.speak(text):
                        return True
                except Exception:
                    # Provider failed, try next one
                    continue
        
        return False


def load_tts(
    priority: Optional[List[str]] = None,
    voice_gender: VoiceGender = "female"
) -> TTSLoader:
    """
    Convenience function to create a TTSLoader instance.
    
    Args:
        priority: List of provider names in order of preference
        voice_gender: Preferred voice gender (male/female)
        
    Returns:
        Configured TTSLoader instance
    """
    # Check environment for voice gender override
    env_gender = os.getenv("TTS_VOICE_GENDER")
    if env_gender and env_gender.lower() in ["male", "female"]:
        voice_gender = env_gender.lower()  # type: ignore
    
    return TTSLoader(priority=priority, voice_gender=voice_gender)