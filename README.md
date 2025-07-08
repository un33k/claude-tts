# claude-tts

A multi-provider Text-to-Speech (TTS) package designed for seamless integration with Claude Code hooks. Supports multiple TTS providers with automatic fallback and minimal configuration.

## Features

- 🎯 **Multiple TTS Providers**: ElevenLabs, OpenAI, and pyttsx3 (offline)
- 🔄 **Automatic Fallback**: Seamlessly switches between providers based on availability
- 🎣 **Claude Code Integration**: Built-in hook support for Claude Code notifications
- 🔧 **Minimal Configuration**: Works out-of-the-box with sensible defaults
- 🌐 **Environment-based Config**: Easy setup via environment variables
- 🎨 **Voice Customization**: Support for male/female voice selection
- 📦 **Modular Installation**: Install only the providers you need

## Installation

### Basic Installation (offline TTS only)
```bash
pip install claude-tts
```

### With Specific Providers
```bash
# With pyttsx3 (offline)
pip install claude-tts[pyttsx3]

# With ElevenLabs
pip install claude-tts[elevenlabs]

# With OpenAI
pip install claude-tts[openai]

# With all providers
pip install claude-tts[all]
```

### From GitHub
```bash
pip install git+https://github.com/yourusername/claude-tts.git
```

## Quick Start

### Basic Usage

```python
from claude_tts import load_tts

# Initialize with defaults (uses pyttsx3 if available)
tts = load_tts()

# Speak text using the best available provider
tts.speak("Hello from Claude TTS!")

# List available providers
print(tts.list_available())  # ['pyttsx3', 'elevenlabs', 'openai']

# Use a specific provider
tts.speak("Using ElevenLabs", provider_name="elevenlabs")

# Initialize with custom settings
tts = load_tts(
    priority=['elevenlabs', 'pyttsx3', 'openai'],
    voice_gender='male'
)
```

### Claude Code Hook Integration

#### Method 1: Using the built-in CLI command

Add to your `.claude/settings.json`:
```json
{
  "hooks": {
    "Notification": [{
      "hooks": [{
        "type": "command",
        "command": "claude-tts"
      }]
    }]
  }
}
```

#### Method 2: Custom hook script

Create `.claude/hooks/tts_notification.py`:
```python
#!/usr/bin/env python3
from claude_tts.hooks import tts_notification_hook

if __name__ == "__main__":
    # Optional: customize behavior
    tts_notification_hook(
        priority=['pyttsx3', 'elevenlabs'],
        voice_gender='female'
    )
```

Then in `.claude/settings.json`:
```json
{
  "hooks": {
    "Notification": [{
      "hooks": [{
        "type": "command",
        "command": "python .claude/hooks/tts_notification.py"
      }]
    }]
  }
}
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# API Keys
ELEVENLABS_API_KEY=your_elevenlabs_api_key
OPENAI_API_KEY=your_openai_api_key

# TTS Settings
TTS_PRIORITY=pyttsx3,elevenlabs,openai
TTS_VOICE_GENDER=female

# Provider-specific settings
TTS_ELEVENLABS_VOICE_ID=custom_voice_id
TTS_OPENAI_MODEL=gpt-4o-mini-tts
```

### Programmatic Configuration

```python
from claude_tts import load_tts

# Configure priority and voice
tts = load_tts(
    priority=['elevenlabs', 'openai', 'pyttsx3'],
    voice_gender='male'
)

# Get specific provider
provider = tts.get_provider()
print(f"Using: {provider.name}")
```

## API Reference

### TTSLoader

The main class for managing TTS providers.

```python
class TTSLoader:
    def __init__(self, priority: Optional[List[str]] = None, voice_gender: VoiceGender = "female"):
        """Initialize with provider priority and voice preference."""
    
    def speak(self, text: str, provider_name: Optional[str] = None) -> bool:
        """Speak text using specified or best available provider."""
    
    def get_provider(self) -> Optional[TTSProvider]:
        """Get the first available provider based on priority."""
    
    def list_available(self) -> List[str]:
        """List all available provider names."""
```

### Provider Interface

All providers implement this interface:

```python
class TTSProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
    
    @abstractmethod
    def speak(self, text: str) -> bool:
        """Speak the given text."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
```

## Provider Details

### pyttsx3 (Offline)
- **Pros**: No API key required, works offline, free
- **Cons**: Limited voice options, platform-dependent voices
- **Best for**: Local development, offline usage

### ElevenLabs
- **Pros**: High-quality voices, multiple languages, voice cloning
- **Cons**: Requires API key, costs per character
- **Best for**: Production use with high-quality requirements
- **Voices**: Antoni (male), Rachel (female)

### OpenAI
- **Pros**: Good quality, integrated with OpenAI ecosystem
- **Cons**: Requires API key, costs per character
- **Best for**: Projects already using OpenAI
- **Voices**: Onyx (male), Nova (female)

## Advanced Usage

### Adding Custom Providers

```python
from claude_tts.providers.base import TTSProvider
from claude_tts import TTSLoader

class CustomProvider(TTSProvider):
    @property
    def name(self) -> str:
        return "custom"
    
    def is_available(self) -> bool:
        # Check if your provider is available
        return True
    
    def speak(self, text: str) -> bool:
        # Implement TTS logic
        print(f"Speaking: {text}")
        return True

# Register custom provider
tts = TTSLoader()
tts.providers['custom'] = CustomProvider()
```

### Error Handling

```python
from claude_tts import load_tts

tts = load_tts()

# Check if any provider is available
if not tts.get_provider():
    print("No TTS providers available!")
    
# Handle speak failures
if not tts.speak("Hello"):
    print("Failed to speak - all providers failed")
```

## Development

### Project Structure
```
claude-tts/
├── src/claude_tts/
│   ├── __init__.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── elevenlabs.py
│   │   ├── openai.py
│   │   └── pyttsx3.py
│   ├── loader.py
│   └── hooks.py
├── tests/
├── examples/
└── pyproject.toml
```

### Running Tests
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=claude_tts
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests: `pytest`
5. Commit: `git commit -am 'Add feature'`
6. Push: `git push origin feature-name`
7. Create a Pull Request

### Adding New Providers

1. Create a new file in `src/claude_tts/providers/`
2. Inherit from `TTSProvider` base class
3. Implement required methods: `name`, `is_available()`, `speak()`
4. Add to providers dict in `loader.py`
5. Update documentation

## Troubleshooting

### No Audio on macOS
- Check System Preferences > Security & Privacy > Privacy > Speech Recognition
- Ensure your terminal has permission to use speech

### API Key Issues
- Ensure environment variables are set correctly
- Check `.env` file is in the project root
- Verify API keys are valid

### Provider Not Available
```python
# Debug provider availability
tts = load_tts()
for name, provider in tts.providers.items():
    print(f"{name}: {'✓' if provider.is_available() else '✗'}")
```

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built for seamless integration with [Claude Code](https://github.com/anthropics/claude-code)
- Inspired by the need for flexible TTS in AI-assisted development

## Changelog

### v0.1.0
- Initial release
- Support for ElevenLabs, OpenAI, and pyttsx3
- Claude Code hook integration
- Basic fallback mechanism