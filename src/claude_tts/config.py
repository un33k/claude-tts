"""Configuration handling for claude-tts."""

import os
from pathlib import Path
from typing import Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    
    # Look for .env file in current directory and parent directories
    current_path = Path.cwd()
    env_file = None
    
    for parent in [current_path] + list(current_path.parents):
        potential_env = parent / ".env"
        if potential_env.exists():
            env_file = potential_env
            break
    
    if env_file:
        load_dotenv(env_file)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for a specific provider.
    
    Args:
        provider: The provider name (elevenlabs, openai, gemini)
        
    Returns:
        The API key if found, None otherwise
    """
    key_mappings = {
        "elevenlabs": ["ELEVENLABS_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "gemini": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    }
    
    keys_to_check = key_mappings.get(provider, [])
    
    for key_name in keys_to_check:
        api_key = os.getenv(key_name)
        if api_key:
            return api_key
    
    return None


def get_provider_priority() -> list[str]:
    """
    Get the provider priority from environment.
    
    Returns:
        List of provider names in priority order
    """
    env_priority = os.getenv("TTS_PRIORITY")
    if env_priority:
        return [p.strip() for p in env_priority.split(",")]
    return ["pyttsx3", "elevenlabs", "openai", "gemini"]


def get_voice_gender() -> str:
    """
    Get the default voice gender from environment.
    
    Returns:
        "male" or "female"
    """
    env_gender = os.getenv("TTS_VOICE_GENDER", "female").lower()
    return env_gender if env_gender in ["male", "female"] else "female"