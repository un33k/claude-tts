#!/usr/bin/env python3
"""Example Claude Code hook setup for TTS notifications."""

import json
import os

def setup_claude_code_tts():
    """Set up TTS for Claude Code notifications."""
    
    # Path to Claude Code settings
    claude_dir = os.path.expanduser("~/.claude")
    settings_file = os.path.join(claude_dir, "settings.json")
    
    # Create .claude directory if it doesn't exist
    os.makedirs(claude_dir, exist_ok=True)
    
    # Load existing settings or create new
    settings = {}
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    
    # Add TTS hook for notifications
    if "hooks" not in settings:
        settings["hooks"] = {}
    
    if "Notification" not in settings["hooks"]:
        settings["hooks"]["Notification"] = []
    
    # Add our TTS command
    tts_hook = {
        "hooks": [{
            "type": "command",
            "command": "claude-tts"
        }]
    }
    
    # Check if already added
    already_added = any(
        hook.get("hooks", [{}])[0].get("command") == "claude-tts"
        for hook in settings["hooks"]["Notification"]
        if isinstance(hook, dict) and "hooks" in hook
    )
    
    if not already_added:
        settings["hooks"]["Notification"].append(tts_hook)
        
        # Save settings
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        print(f"✓ Added TTS hook to {settings_file}")
    else:
        print("✓ TTS hook already configured")
    
    # Create example .env file if needed
    env_example = """# Example .env file for claude-tts

# API Keys (uncomment and add your keys)
# ELEVENLABS_API_KEY=your_elevenlabs_api_key
# OPENAI_API_KEY=your_openai_api_key
# GOOGLE_API_KEY=your_google_api_key

# TTS Settings
TTS_PRIORITY=pyttsx3,elevenlabs,openai,gemini
TTS_VOICE_GENDER=female

# Provider-specific settings
# TTS_ELEVENLABS_VOICE_ID=custom_voice_id
# TTS_OPENAI_MODEL=tts-1
"""
    
    env_file = os.path.join(claude_dir, ".env.example")
    with open(env_file, 'w') as f:
        f.write(env_example)
    
    print(f"✓ Created example .env file at {env_file}")
    print("\nTo use API-based TTS providers:")
    print(f"1. Copy {env_file} to {os.path.join(claude_dir, '.env')}")
    print("2. Add your API keys")
    print("3. Restart Claude Code")

if __name__ == "__main__":
    setup_claude_code_tts()