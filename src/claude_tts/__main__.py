"""CLI entry point for claude-tts."""

import argparse
import json
import logging
import sys
from typing import Optional

from . import load_tts, VoiceGender
from .config import get_provider_priority, get_voice_gender


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude TTS - Multi-provider text-to-speech tool"
    )
    
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to speak. If not provided, reads from stdin or Claude Code event"
    )
    
    parser.add_argument(
        "-p", "--provider",
        choices=["pyttsx3", "elevenlabs", "openai", "gemini"],
        help="Specific TTS provider to use"
    )
    
    parser.add_argument(
        "-g", "--gender",
        choices=["male", "female"],
        default=get_voice_gender(),
        help="Voice gender preference (default: from env or female)"
    )
    
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available TTS providers"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--priority",
        help="Comma-separated list of providers in priority order"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Parse priority if provided
    priority = None
    if args.priority:
        priority = [p.strip() for p in args.priority.split(",")]
    
    # Initialize TTS loader
    tts = load_tts(priority=priority, voice_gender=args.gender)  # type: ignore
    
    # Handle list command
    if args.list:
        available = tts.list_available()
        if available:
            print("Available TTS providers:")
            for provider_name in available:
                provider = tts.get_provider(provider_name)
                if provider:
                    print(f"  - {provider_name}")
        else:
            print("No TTS providers available")
        return
    
    # Get text to speak
    text = args.text
    
    if not text:
        # Check if this is a Claude Code hook event
        if sys.stdin.isatty():
            # Interactive mode - prompt for text
            try:
                text = input("Enter text to speak: ")
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled")
                return
        else:
            # Read from stdin (could be Claude Code event)
            stdin_data = sys.stdin.read().strip()
            
            # Try to parse as JSON (Claude Code event format)
            try:
                event = json.loads(stdin_data)
                # Extract text from various event types
                if isinstance(event, dict):
                    # Look for common fields in Claude Code events
                    text = (
                        event.get("message") or
                        event.get("text") or 
                        event.get("content") or
                        event.get("description") or
                        str(event)
                    )
                else:
                    text = stdin_data
            except json.JSONDecodeError:
                # Not JSON, use as-is
                text = stdin_data
    
    if not text:
        print("No text provided")
        sys.exit(1)
    
    # Speak the text
    success = tts.speak(text, provider_name=args.provider)
    
    if not success:
        print("Failed to speak text - no available TTS provider", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()