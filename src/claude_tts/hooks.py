"""Claude Code hook integration for TTS notifications."""

import json
import logging
import sys
from typing import Any, Dict, Optional

from . import load_tts, VoiceGender

logger = logging.getLogger(__name__)


def parse_claude_event(event_data: str) -> Optional[str]:
    """
    Parse a Claude Code event and extract text to speak.
    
    Args:
        event_data: Raw event data from Claude Code
        
    Returns:
        Text to speak, or None if no text found
    """
    try:
        event = json.loads(event_data)
        
        if not isinstance(event, dict):
            return str(event)
        
        # Handle different event types
        event_type = event.get("type", "").lower()
        
        # Notification events
        if "notification" in event_type:
            # Look for message, content, or text fields
            return (
                event.get("message") or
                event.get("content") or
                event.get("text") or
                event.get("body") or
                f"Claude notification: {event.get('title', 'Event')}"
            )
        
        # Task completion events
        if "complete" in event_type or "done" in event_type:
            task = event.get("task") or event.get("name") or "Task"
            return f"{task} completed"
        
        # Error events
        if "error" in event_type or "fail" in event_type:
            error = event.get("error") or event.get("message") or "Error occurred"
            return f"Error: {error}"
        
        # Generic event handling
        return (
            event.get("message") or
            event.get("text") or
            event.get("content") or
            event.get("description") or
            f"Claude event: {event_type or 'notification'}"
        )
        
    except json.JSONDecodeError:
        # Not JSON, return as-is
        return event_data.strip() if event_data else None
    except Exception as e:
        logger.error(f"Failed to parse Claude event: {e}")
        return None


def tts_notification_hook(
    priority: Optional[list[str]] = None,
    voice_gender: VoiceGender = "female",
    fallback_message: str = "Claude notification"
) -> None:
    """
    Claude Code notification hook that speaks events.
    
    This function is designed to be called from Claude Code hooks.
    It reads event data from stdin and speaks it using available TTS.
    
    Args:
        priority: Optional provider priority list
        voice_gender: Voice gender preference
        fallback_message: Message to speak if no text extracted
    """
    # Set up minimal logging
    logging.basicConfig(level=logging.WARNING)
    
    try:
        # Read event data from stdin
        if sys.stdin.isatty():
            # Not being called as a hook
            print("This function should be called from Claude Code hooks")
            return
        
        event_data = sys.stdin.read()
        
        # Parse the event to get text
        text = parse_claude_event(event_data)
        
        if not text:
            text = fallback_message
        
        # Initialize TTS and speak
        tts = load_tts(priority=priority, voice_gender=voice_gender)
        
        # Try to speak with fallback
        if not tts.speak(text):
            # Log failure but don't crash the hook
            logger.warning("Failed to speak notification")
    
    except Exception as e:
        # Never let the hook crash Claude Code
        logger.error(f"TTS hook error: {e}")


def create_hook_script(
    output_path: str,
    priority: Optional[list[str]] = None,
    voice_gender: VoiceGender = "female"
) -> None:
    """
    Create a standalone hook script for Claude Code.
    
    Args:
        output_path: Path where to save the hook script
        priority: Optional provider priority list
        voice_gender: Voice gender preference
    """
    priority_str = str(priority) if priority else "None"
    
    script_content = f'''#!/usr/bin/env python3
"""Claude Code TTS notification hook."""

from claude_tts.hooks import tts_notification_hook

if __name__ == "__main__":
    tts_notification_hook(
        priority={priority_str},
        voice_gender="{voice_gender}"
    )
'''
    
    with open(output_path, 'w') as f:
        f.write(script_content)
    
    # Make executable on Unix-like systems
    import os
    import stat
    
    try:
        st = os.stat(output_path)
        os.chmod(output_path, st.st_mode | stat.S_IEXEC)
    except:
        pass