"""Google Gemini TTS provider."""

import logging
import os
import tempfile
from typing import Optional

from .base import TTSProvider
from ..types import VoiceGender

logger = logging.getLogger(__name__)


class GeminiProvider(TTSProvider):
    """TTS provider using Google's Gemini/Cloud Text-to-Speech API."""
    
    # Voice name patterns for each gender
    VOICE_PATTERNS = {
        "male": {
            "name": "en-US-Standard-D",
            "language_code": "en-US"
        },
        "female": {
            "name": "en-US-Standard-C", 
            "language_code": "en-US"
        }
    }
    
    def __init__(self, voice_gender: VoiceGender = "female"):
        """Initialize the Gemini provider."""
        super().__init__(voice_gender)
        self._client: Optional[object] = None
        self._voice_config = self.VOICE_PATTERNS.get(voice_gender, self.VOICE_PATTERNS["female"])
        self._api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self._available = self._check_availability()
    
    @property
    def name(self) -> str:
        """Return the provider name."""
        return "gemini"
    
    def _check_availability(self) -> bool:
        """Check if Gemini/Google Cloud TTS is available."""
        if not self._api_key:
            logger.debug("Google/Gemini API key not found")
            return False
        
        try:
            import google.generativeai as genai
            return True
        except ImportError:
            # Try alternative: Google Cloud Text-to-Speech
            try:
                from google.cloud import texttospeech
                return True
            except ImportError:
                logger.debug("google-generativeai or google-cloud-texttospeech package not installed")
                return False
        except Exception as e:
            logger.debug(f"Gemini not available: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if the provider is available."""
        return self._available
    
    def speak(self, text: str) -> bool:
        """
        Speak the given text using Gemini/Google Cloud TTS.
        
        Args:
            text: The text to speak
            
        Returns:
            True if successful, False otherwise
        """
        # Try using Google Cloud Text-to-Speech first
        if self._try_cloud_tts(text):
            return True
        
        # Fallback to using Gemini API if available
        # Note: As of now, Gemini doesn't have direct TTS, but this is future-proofing
        logger.warning("Gemini direct TTS not yet available, falling back to Cloud TTS")
        return False
    
    def _try_cloud_tts(self, text: str) -> bool:
        """Try to use Google Cloud Text-to-Speech."""
        try:
            from google.cloud import texttospeech
            
            # Initialize client with API key
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self._api_key
            client = texttospeech.TextToSpeechClient()
            
            # Set up the text input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code=self._voice_config["language_code"],
                name=self._voice_config["name"],
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE if self.voice_gender == "female" else texttospeech.SsmlVoiceGender.MALE
            )
            
            # Select the audio format
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Perform the text-to-speech request
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save to temporary file and play
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(response.audio_content)
                tmp_path = tmp_file.name
            
            return self._play_audio(tmp_path)
            
        except Exception as e:
            logger.debug(f"Google Cloud TTS failed: {e}")
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