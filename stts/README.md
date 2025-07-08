# @ehaye/stts - Smart Text-to-Speech Installer

🎯 **Smart TTS installer for development tools** - Automatically detects and configures TTS hooks for Claude Code and other development environments.

## Features

- 🔍 **Auto-Detection**: Detects installed development tools (Claude Code, etc.)
- 🪝 **Smart Hook Installation**: Configures all available hooks automatically
- 🔊 **Multi-Provider TTS**: Uses @claude-code/tts with fallback support
- 📊 **Event Logging**: JSON-based event logging for analytics
- 🛡️ **Security**: Blocks dangerous commands before execution
- 🎭 **Customizable**: Environment-based configuration

## Installation

```bash
npm install -g @ehaye/stts
```

## Quick Start

### 1. Detect Claude Code
```bash
stts detect claude-code
# or just detect all tools
stts detect
```

### 2. Enable TTS Hooks
```bash
stts enable claude-code
```

### 3. Test TTS
```bash
stts test
```

### 4. Check Status
```bash
stts status
```

## Commands

### `stts detect [tool]`
Detects installed development tools.

```bash
# Detect specific tool
stts detect claude-code

# Detect all supported tools
stts detect

# Output as JSON
stts detect --json
```

### `stts enable <tool>`
Installs TTS hooks for the specified tool.

```bash
stts enable claude-code
```

This installs hooks for:
- **PreToolUse**: Announces tool usage and blocks dangerous commands
- **PostToolUse**: Reports completion of long-running tasks
- **Notification**: Speaks all notifications
- **Stop**: Announces session completion
- **SubagentStop**: Announces agent task completion

### `stts disable <tool>`
Removes TTS hooks for the specified tool.

```bash
stts disable claude-code
```

### `stts status`
Shows TTS status for all detected tools.

```bash
stts status
```

### `stts test`
Tests TTS functionality.

```bash
# Default test
stts test

# Custom message
stts test --message "Hello from STTS"
```

## Hook Details

### PreToolUse Hook
- Announces which tool is being run
- Blocks dangerous commands (rm -rf, format, etc.)
- Logs all tool usage for analytics

### PostToolUse Hook
- Tracks execution time
- Announces completion of long tasks (>5 seconds)
- Logs performance metrics

### Notification Hook
- Speaks all Claude Code notifications
- Logs notification events
- Silent failures (won't break on TTS errors)

### Stop Hook
- Announces session completion
- Provides variety in completion messages

### SubagentStop Hook
- Announces when agent tasks complete
- Tracks agent performance

## Configuration

### Environment Variables

Create a `.env` file in your project or home directory:

```bash
# TTS Configuration (from @claude-code/tts)
TTS_PRIORITY=say,elevenlabs,openai
TTS_VOICE_GENDER=female
ELEVENLABS_API_KEY=your_api_key
OPENAI_API_KEY=your_api_key

# Debug mode
DEBUG=true
```

### Logging

Logs are stored in `~/.stts/logs/`:
- `notification.json` - All notifications
- `pre-tool-use.json` - Tool usage events
- `post-tool-use.json` - Tool completion events
- `stop.json` - Session events
- `subagent-stop.json` - Agent events

## Security Features

The PreToolUse hook blocks dangerous commands:
- `rm -rf` operations
- Disk formatting commands
- Fork bombs
- System-wide permission changes

When a dangerous command is detected:
1. Command is blocked (exit code 2)
2. Warning is announced via TTS
3. Event is logged for review

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/ehaye/stts.git
cd stts

# Install dependencies
npm install

# Build TypeScript
npm run build

# Link for local testing
npm link
```

### Testing Hooks Manually

```bash
# Test notification hook
echo '{"message": "Test notification"}' | node dist/hooks/notification.js

# Test pre-tool-use hook
echo '{"tool": "bash", "args": {"command": "ls -la"}}' | node dist/hooks/pre-tool-use.js
```

## Troubleshooting

### "Tool not found"
- Ensure the tool is installed and in your PATH
- Try `which claude-code` or `which claude`

### "Could not find settings file"
- Check if `~/.claude/settings.json` exists
- Run the tool from a directory with `.claude` folder

### TTS not working
- Check available providers: `stts test`
- Verify API keys in `.env` file
- Check system audio settings

### Hooks not triggering
- Verify installation: `stts status`
- Check Claude Code is using the correct settings file
- Review logs in `~/.stts/logs/`

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Add tests for new functionality
4. Submit a pull request

---

**Built to enhance the Claude Code experience with audio feedback**