"""OpenAI TTS provider."""

import logging
import os
import tempfile
from typing import Optional

from .base import TTSProvider
from ..types import VoiceGender

logger = logging.getLogger(__name__)


class OpenAIProvider(TTSProvider):
    """TTS provider using OpenAI's text-to-speech API."""
    
    # Voice mappings for each gender
    VOICES = {
        "male": "onyx",
        "female": "nova"
    }
    
    def __init__(self, voice_gender: VoiceGender = "female"):
        """Initialize the OpenAI provider."""
        super().__init__(voice_gender)
        self._client: Optional[object] = None
        self._voice = self.VOICES.get(voice_gender, "nova")
        self._api_key = os.getenv("OPENAI_API_KEY")
        self._model = os.getenv("TTS_OPENAI_MODEL", "tts-1")
        self._available = self._check_availability()
    
    @property
    def name(self) -> str:
        """Return the provider name."""
        return "openai"
    
    def _check_availability(self) -> bool:
        """Check if OpenAI is available."""
        if not self._api_key:
            logger.debug("OpenAI API key not found")
            return False
        
        try:
            from openai import OpenAI
            return True
        except ImportError:
            logger.debug("openai package not installed")
            return False
        except Exception as e:
            logger.debug(f"OpenAI not available: {e}")
            return False
    
    def _get_client(self) -> Optional[object]:
        """Get or create the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                return None
        return self._client
    
    def is_available(self) -> bool:
        """Check if the provider is available."""
        return self._available
    
    def speak(self, text: str) -> bool:
        """
        Speak the given text using OpenAI TTS.
        
        Args:
            text: The text to speak
            
        Returns:
            True if successful, False otherwise
        """
        client = self._get_client()
        if not client:
            return False
        
        try:
            # Generate speech
            response = client.audio.speech.create(
                model=self._model,
                voice=self._voice,
                input=text
            )
            
            # Save to temporary file and play
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            # Play the audio file
            return self._play_audio(tmp_path)
            
        except Exception as e:
            logger.error(f"OpenAI speak failed: {e}")
            return False
    
    def _play_audio(self, file_path: str) -> bool:
        """Play an audio file using system audio player."""
        try:
            import platform
            import subprocess
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", file_path], check=True)
            elif system == "Linux":
                # Try multiple audio players
                for player in ["aplay", "paplay", "play"]:
                    try:
                        subprocess.run([player, file_path], check=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif system == "Windows":
                # Use Windows Media Player
                subprocess.run(
                    ["powershell", "-c", f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()"],
                    check=True
                )
            else:
                logger.error(f"Unsupported platform: {system}")
                return False
            
            # Clean up the temporary file
            os.unlink(file_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            # Try to clean up
            try:
                os.unlink(file_path)
            except:
                pass
            return False