#!/usr/bin/env python3
"""Basic usage example for claude-tts."""

from claude_tts import load_tts

def main():
    # Initialize with defaults (uses pyttsx3 if available)
    tts = load_tts()
    
    # List available providers
    print("Available TTS providers:")
    for provider in tts.list_available():
        print(f"  - {provider}")
    print()
    
    # Speak using the best available provider
    print("Speaking with best available provider...")
    success = tts.speak("Hello from Claude TTS! This is a test of the text to speech system.")
    
    if success:
        print("✓ Speech successful")
    else:
        print("✗ No TTS provider available")
    
    # Try specific providers
    providers_to_test = ["pyttsx3", "elevenlabs", "openai", "gemini"]
    
    for provider_name in providers_to_test:
        if provider_name in tts.list_available():
            print(f"\nTesting {provider_name} provider...")
            success = tts.speak(f"This is the {provider_name} provider speaking", provider_name=provider_name)
            if success:
                print(f"✓ {provider_name} worked")
            else:
                print(f"✗ {provider_name} failed")

if __name__ == "__main__":
    main()