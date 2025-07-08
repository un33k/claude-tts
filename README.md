// package.json
{
  "name": "@claude-code/tts",
  "version": "1.0.0",
  "description": "Text-to-Speech plugin for Claude Code with multiple provider support",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "bin": {
    "claude-tts": "dist/bin/cli.js",
    "claude-tts-install": "dist/bin/install.js"
  },
  "scripts": {
    "build": "tsc",
    "prepublishOnly": "npm run build",
    "postinstall": "node dist/bin/install.js",
    "test": "jest"
  },
  "keywords": ["claude-code", "tts", "text-to-speech", "ai"],
  "author": "Your Name",
  "license": "MIT",
  "dependencies": {
    "dotenv": "^16.0.0",
    "axios": "^1.6.0",
    "say": "^0.16.0",
    "commander": "^11.0.0",
    "chalk": "^4.1.2"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "jest": "^29.0.0",
    "@types/jest": "^29.0.0"
  },
  "optionalDependencies": {
    "elevenlabs": "^0.7.0",
    "openai": "^4.20.0"
  },
  "files": [
    "dist/**/*",
    "README.md",
    "LICENSE"
  ]
}

// src/types.ts
export type VoiceGender = 'male' | 'female';

export interface TTSConfig {
  priority?: string[];
  voiceGender?: VoiceGender;
  elevenLabsApiKey?: string;
  openaiApiKey?: string;
  elevenLabsVoiceId?: string;
  openaiModel?: string;
}

export interface TTSProvider {
  readonly name: string;
  isAvailable(): Promise<boolean>;
  speak(text: string): Promise<boolean>;
}

// src/providers/base.ts
export abstract class BaseTTSProvider implements TTSProvider {
  abstract readonly name: string;
  
  constructor(protected config: TTSConfig) {}
  
  abstract isAvailable(): Promise<boolean>;
  abstract speak(text: string): Promise<boolean>;
}

// src/providers/say.ts
import { spawn } from 'child_process';
import { BaseTTSProvider } from './base.js';

export class SayProvider extends BaseTTSProvider {
  readonly name = 'say';
  
  async isAvailable(): Promise<boolean> {
    try {
      const say = await import('say');
      return !!say.default;
    } catch {
      return false;
    }
  }
  
  async speak(text: string): Promise<boolean> {
    try {
      const say = await import('say');
      const voice = this.getVoice();
      
      return new Promise((resolve) => {
        say.default.speak(text, voice, (err) => {
          resolve(!err);
        });
      });
    } catch (error) {
      console.error('Say provider error:', error);
      return false;
    }
  }
  
  private getVoice(): string | undefined {
    const platform = process.platform;
    const gender = this.config.voiceGender || 'female';
    
    if (platform === 'darwin') { // macOS
      return gender === 'male' ? 'Alex' : 'Samantha';
    } else if (platform === 'win32') { // Windows
      return gender === 'male' ? 'David' : 'Zira';
    } else { // Linux
      return gender === 'male' ? 'male' : 'female';
    }
  }
}

// src/providers/elevenlabs.ts
import { BaseTTSProvider } from './base.js';

export class ElevenLabsProvider extends BaseTTSProvider {
  readonly name = 'elevenlabs';
  private apiKey: string;
  
  constructor(config: TTSConfig) {
    super(config);
    this.apiKey = config.elevenLabsApiKey || process.env.ELEVENLABS_API_KEY || '';
  }
  
  async isAvailable(): Promise<boolean> {
    if (!this.apiKey) return false;
    
    try {
      const axios = await import('axios');
      const response = await axios.default.get('https://api.elevenlabs.io/v1/voices', {
        headers: { 'xi-api-key': this.apiKey },
        timeout: 5000
      });
      return response.status === 200;
    } catch {
      return false;
    }
  }
  
  async speak(text: string): Promise<boolean> {
    try {
      const axios = await import('axios');
      const voiceId = this.getVoiceId();
      
      const response = await axios.default.post(
        `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
        {
          text,
          model_id: 'eleven_monolingual_v1',
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.5
          }
        },
        {
          headers: {
            'Accept': 'audio/mpeg',
            'Content-Type': 'application/json',
            'xi-api-key': this.apiKey
          },
          responseType: 'stream'
        }
      );
      
      // Play the audio stream
      await this.playAudioStream(response.data);
      return true;
    } catch (error) {
      console.error('ElevenLabs provider error:', error);
      return false;
    }
  }
  
  private getVoiceId(): string {
    if (this.config.elevenLabsVoiceId) {
      return this.config.elevenLabsVoiceId;
    }
    
    // Default voices
    const gender = this.config.voiceGender || 'female';
    return gender === 'male' ? 'ErXwobaYiN019PkySvjV' : 'EXAVITQu4vr4xnSDxMaL'; // Antoni : Rachel
  }
  
  private async playAudioStream(audioStream: any): Promise<void> {
    return new Promise((resolve, reject) => {
      const { spawn } = require('child_process');
      
      // Try different audio players based on platform
      const platform = process.platform;
      let playerCmd: string;
      let playerArgs: string[];
      
      if (platform === 'darwin') { // macOS
        playerCmd = 'afplay';
        playerArgs = ['-'];
      } else if (platform === 'win32') { // Windows
        playerCmd = 'powershell';
        playerArgs = ['-c', '(New-Object Media.SoundPlayer).PlaySync()'];
      } else { // Linux
        playerCmd = 'aplay';
        playerArgs = ['-'];
      }
      
      const player = spawn(playerCmd, playerArgs);
      
      audioStream.pipe(player.stdin);
      
      player.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Audio player exited with code ${code}`));
      });
      
      player.on('error', reject);
    });
  }
}

// src/providers/openai.ts
import { BaseTTSProvider } from './base.js';

export class OpenAIProvider extends BaseTTSProvider {
  readonly name = 'openai';
  private apiKey: string;
  
  constructor(config: TTSConfig) {
    super(config);
    this.apiKey = config.openaiApiKey || process.env.OPENAI_API_KEY || '';
  }
  
  async isAvailable(): Promise<boolean> {
    if (!this.apiKey) return false;
    
    try {
      const axios = await import('axios');
      const response = await axios.default.get('https://api.openai.com/v1/models', {
        headers: { 'Authorization': `Bearer ${this.apiKey}` },
        timeout: 5000
      });
      return response.status === 200;
    } catch {
      return false;
    }
  }
  
  async speak(text: string): Promise<boolean> {
    try {
      const axios = await import('axios');
      const voice = this.getVoice();
      const model = this.config.openaiModel || 'tts-1';
      
      const response = await axios.default.post(
        'https://api.openai.com/v1/audio/speech',
        {
          model,
          input: text,
          voice
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          },
          responseType: 'stream'
        }
      );
      
      await this.playAudioStream(response.data);
      return true;
    } catch (error) {
      console.error('OpenAI provider error:', error);
      return false;
    }
  }
  
  private getVoice(): string {
    const gender = this.config.voiceGender || 'female';
    return gender === 'male' ? 'onyx' : 'nova';
  }
  
  private async playAudioStream(audioStream: any): Promise<void> {
    return new Promise((resolve, reject) => {
      const { spawn } = require('child_process');
      
      const platform = process.platform;
      let playerCmd: string;
      let playerArgs: string[];
      
      if (platform === 'darwin') {
        playerCmd = 'afplay';
        playerArgs = ['-'];
      } else if (platform === 'win32') {
        playerCmd = 'powershell';
        playerArgs = ['-c', '(New-Object Media.SoundPlayer).PlaySync()'];
      } else {
        playerCmd = 'aplay';
        playerArgs = ['-'];
      }
      
      const player = spawn(playerCmd, playerArgs);
      audioStream.pipe(player.stdin);
      
      player.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Audio player exited with code ${code}`));
      });
      
      player.on('error', reject);
    });
  }
}

// src/loader.ts
import { TTSProvider, TTSConfig } from './types.js';
import { SayProvider } from './providers/say.js';
import { ElevenLabsProvider } from './providers/elevenlabs.js';
import { OpenAIProvider } from './providers/openai.js';

export class TTSLoader {
  private providers: Map<string, TTSProvider> = new Map();
  private config: TTSConfig;
  
  constructor(config: TTSConfig = {}) {
    this.config = {
      priority: ['say', 'elevenlabs', 'openai'],
      voiceGender: 'female',
      ...config
    };
    
    this.initializeProviders();
  }
  
  private initializeProviders(): void {
    this.providers.set('say', new SayProvider(this.config));
    this.providers.set('elevenlabs', new ElevenLabsProvider(this.config));
    this.providers.set('openai', new OpenAIProvider(this.config));
  }
  
  async speak(text: string, providerName?: string): Promise<boolean> {
    if (providerName) {
      const provider = this.providers.get(providerName);
      if (provider && await provider.isAvailable()) {
        return await provider.speak(text);
      }
      return false;
    }
    
    // Try providers in priority order
    for (const name of this.config.priority!) {
      const provider = this.providers.get(name);
      if (provider && await provider.isAvailable()) {
        return await provider.speak(text);
      }
    }
    
    return false;
  }
  
  async getProvider(): Promise<TTSProvider | null> {
    for (const name of this.config.priority!) {
      const provider = this.providers.get(name);
      if (provider && await provider.isAvailable()) {
        return provider;
      }
    }
    return null;
  }
  
  async listAvailable(): Promise<string[]> {
    const available: string[] = [];
    for (const [name, provider] of this.providers) {
      if (await provider.isAvailable()) {
        available.push(name);
      }
    }
    return available;
  }
}

// src/index.ts
import { config } from 'dotenv';
import { TTSLoader } from './loader.js';
import { TTSConfig } from './types.js';

config(); // Load .env file

export function loadTTS(userConfig: TTSConfig = {}): TTSLoader {
  const envConfig: TTSConfig = {
    priority: process.env.TTS_PRIORITY?.split(',') || undefined,
    voiceGender: (process.env.TTS_VOICE_GENDER as any) || undefined,
    elevenLabsApiKey: process.env.ELEVENLABS_API_KEY,
    openaiApiKey: process.env.OPENAI_API_KEY,
    elevenLabsVoiceId: process.env.TTS_ELEVENLABS_VOICE_ID,
    openaiModel: process.env.TTS_OPENAI_MODEL
  };
  
  const finalConfig = { ...envConfig, ...userConfig };
  return new TTSLoader(finalConfig);
}

export * from './types.js';
export * from './loader.js';

// src/hooks.ts
import { loadTTS } from './index.js';
import { TTSConfig } from './types.js';

export async function ttsNotificationHook(config: TTSConfig = {}): Promise<void> {
  // Read notification data from stdin (Claude Code format)
  const input = await readStdin();
  
  try {
    const notification = JSON.parse(input);
    const message = notification.message || notification.text || 'Notification received';
    
    const tts = loadTTS(config);
    const success = await tts.speak(message);
    
    if (!success) {
      console.error('Failed to speak notification');
      process.exit(1);
    }
  } catch (error) {
    console.error('Error processing notification:', error);
    process.exit(1);
  }
}

function readStdin(): Promise<string> {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    
    process.stdin.on('end', () => {
      resolve(data.trim());
    });
  });
}

// bin/cli.ts
#!/usr/bin/env node
import { Command } from 'commander';
import { loadTTS } from '../src/index.js';
import { ttsNotificationHook } from '../src/hooks.js';
import chalk from 'chalk';

const program = new Command();

program
  .name('claude-tts')
  .description('Text-to-Speech for Claude Code')
  .version('1.0.0');

program
  .command('speak')
  .description('Speak the provided text')
  .argument('<text>', 'Text to speak')
  .option('-p, --provider <provider>', 'TTS provider to use')
  .option('-g, --gender <gender>', 'Voice gender (male/female)', 'female')
  .action(async (text, options) => {
    const tts = loadTTS({ voiceGender: options.gender });
    const success = await tts.speak(text, options.provider);
    
    if (!success) {
      console.error(chalk.red('Failed to speak text'));
      process.exit(1);
    }
  });

program
  .command('list')
  .description('List available TTS providers')
  .action(async () => {
    const tts = loadTTS();
    const available = await tts.listAvailable();
    
    console.log(chalk.blue('Available TTS providers:'));
    available.forEach(provider => {
      console.log(chalk.green(`  ✓ ${provider}`));
    });
    
    if (available.length === 0) {
      console.log(chalk.yellow('  No providers available'));
    }
  });

program
  .command('hook')
  .description('Run as Claude Code notification hook')
  .option('-g, --gender <gender>', 'Voice gender (male/female)', 'female')
  .option('-p, --priority <providers>', 'Provider priority (comma-separated)')
  .action(async (options) => {
    const config = {
      voiceGender: options.gender,
      priority: options.priority?.split(',')
    };
    
    await ttsNotificationHook(config);
  });

// Default action - run as hook
if (process.argv.length === 2) {
  ttsNotificationHook();
} else {
  program.parse();
}

// bin/install.ts
#!/usr/bin/env node
import { promises as fs } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import chalk from 'chalk';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function findClaudeDirectory(): Promise<string | null> {
  let currentDir = process.cwd();
  
  while (currentDir !== '/') {
    const claudeDir = join(currentDir, '.claude');
    try {
      await fs.access(claudeDir);
      return claudeDir;
    } catch {
      currentDir = dirname(currentDir);
    }
  }
  
  return null;
}

async function setupClaudeHook(): Promise<void> {
  const claudeDir = await findClaudeDirectory();
  
  if (!claudeDir) {
    console.log(chalk.yellow('No .claude directory found. Run this in a Claude Code project.'));
    return;
  }
  
  const settingsPath = join(claudeDir, 'settings.json');
  
  try {
    let settings: any = {};
    
    // Read existing settings
    try {
      const existingSettings = await fs.readFile(settingsPath, 'utf8');
      settings = JSON.parse(existingSettings);
    } catch {
      // File doesn't exist or is invalid, start fresh
    }
    
    // Initialize hooks structure
    if (!settings.hooks) {
      settings.hooks = {};
    }
    
    if (!settings.hooks.Notification) {
      settings.hooks.Notification = [];
    }
    
    // Check if our hook already exists
    const existingHook = settings.hooks.Notification.find((hook: any) => 
      hook.hooks?.some((h: any) => h.command === 'claude-tts hook')
    );
    
    if (!existingHook) {
      // Add our TTS hook
      settings.hooks.Notification.push({
        hooks: [{
          type: "command",
          command: "claude-tts hook"
        }]
      });
      
      // Write updated settings
      await fs.writeFile(settingsPath, JSON.stringify(settings, null, 2));
      console.log(chalk.green('✓ Claude TTS hook installed successfully!'));
      console.log(chalk.blue(`  Updated: ${settingsPath}`));
    } else {
      console.log(chalk.yellow('Claude TTS hook already installed.'));
    }
    
    // Create example .env file
    const envPath = join(dirname(claudeDir), '.env.example');
    const envContent = `# Claude TTS Configuration
# Uncomment and fill in the API keys you want to use

# ElevenLabs (high quality, paid)
# ELEVENLABS_API_KEY=your_elevenlabs_api_key
# TTS_ELEVENLABS_VOICE_ID=custom_voice_id

# OpenAI (good quality, paid)  
# OPENAI_API_KEY=your_openai_api_key
# TTS_OPENAI_MODEL=tts-1

# General TTS Settings
TTS_PRIORITY=say,elevenlabs,openai
TTS_VOICE_GENDER=female
`;
    
    try {
      await fs.access(envPath);
    } catch {
      await fs.writeFile(envPath, envContent);
      console.log(chalk.blue(`✓ Created example environment file: ${envPath}`));
    }
    
  } catch (error) {
    console.error(chalk.red('Error setting up Claude hook:'), error);
    process.exit(1);
  }
}

// Run installation if called directly
if (process.argv[1].endsWith('install.js')) {
  setupClaudeHook();
}

export { setupClaudeHook };

// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "node",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "resolveJsonModule": true,
    "allowSyntheticDefaultImports": true
  },
  "include": [
    "src/**/*",
    "bin/**/*"
  ],
  "exclude": [
    "node_modules",
    "dist",
    "**/*.test.ts"
  ]
}

// README.md
# @claude-code/tts

🎯 **Text-to-Speech for Claude Code** - Seamless TTS integration with automatic provider fallback and zero-config setup.

## Features

- 🚀 **Auto-Installation**: Automatically configures Claude Code hooks on install
- 🎯 **Multiple Providers**: Local (say), ElevenLabs, and OpenAI TTS
- 🔄 **Smart Fallback**: Automatically uses the best available provider
- 🎛️ **Zero Config**: Works out-of-the-box with sensible defaults
- 🔧 **Configurable**: Environment variables and programmatic configuration
- 🎨 **Voice Selection**: Male/female voice options per provider
- 📦 **TypeScript**: Full type safety and modern ES modules

## Quick Start

### Installation

```bash
npm install @claude-code/tts
```

That's it! The package will automatically:
1. Find your `.claude` directory
2. Add the TTS notification hook to your `settings.json`
3. Create a `.env.example` file with configuration options

### Basic Usage

```bash
# Test TTS from command line
npx claude-tts speak "Hello from Claude TTS!"

# List available providers
npx claude-tts list

# Use specific provider
npx claude-tts speak "Using ElevenLabs" --provider elevenlabs
```

### Programmatic Usage

```typescript
import { loadTTS } from '@claude-code/tts';

// Basic usage
const tts = loadTTS();
await tts.speak("Hello from TypeScript!");

// With configuration
const tts = loadTTS({
  priority: ['elevenlabs', 'say', 'openai'],
  voiceGender: 'male'
});

// Check available providers
const available = await tts.listAvailable();
console.log('Available:', available);

// Use specific provider
await tts.speak("Custom message", 'elevenlabs');
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# API Keys (optional - only needed for cloud providers)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
OPENAI_API_KEY=your_openai_api_key

# TTS Settings
TTS_PRIORITY=say,elevenlabs,openai
TTS_VOICE_GENDER=female

# Provider-specific settings
TTS_ELEVENLABS_VOICE_ID=custom_voice_id
TTS_OPENAI_MODEL=tts-1
```

### Claude Code Integration

The package automatically adds this to your `.claude/settings.json`:

```json
{
  "hooks": {
    "Notification": [{
      "hooks": [{
        "type": "command",
        "command": "claude-tts hook"
      }]
    }]
  }
}
```

### Manual Hook Configuration

For custom setups, you can also configure manually:

```json
{
  "hooks": {
    "Notification": [{
      "hooks": [{
        "type": "command",
        "command": "claude-tts hook --gender male --priority say,elevenlabs"
      }]
    }]
  }
}
```

## Providers

### Local TTS (`say`)
- ✅ **Pros**: No API key, works offline, free, fast
- ❌ **Cons**: Platform-dependent voices, basic quality
- 🎯 **Best for**: Development, offline use, quick feedback
- 🔧 **Setup**: Included by default (uses system TTS)

### ElevenLabs
- ✅ **Pros**: Premium quality, natural voices, multiple languages
- ❌ **Cons**: Requires API key, costs per character
- 🎯 **Best for**: Production, professional demos, high-quality needs
- 🔧 **Setup**: Set `ELEVENLABS_API_KEY` environment variable

### OpenAI TTS
- ✅ **Pros**: Good quality, integrated ecosystem, reliable
- ❌ **Cons**: Requires API key, costs per character
- 🎯 **Best for**: Projects already using OpenAI, consistent quality
- 🔧 **Setup**: Set `OPENAI_API_KEY` environment variable

## CLI Commands

```bash
# Speak text
claude-tts speak "Your message here"
claude-tts speak "Hello" --provider elevenlabs --gender male

# List available providers
claude-tts list

# Test as notification hook (for debugging)
echo '{"message": "Test notification"}' | claude-tts hook

# Install/update Claude Code hook
claude-tts-install
```

## API Reference

### `loadTTS(config?)`

Creates a new TTS loader instance.

```typescript
interface TTSConfig {
  priority?: string[];           // Provider priority order
  voiceGender?: 'male' | 'female'; // Voice preference
  elevenLabsApiKey?: string;     // ElevenLabs API key
  openaiApiKey?: string;         // OpenAI API key
  elevenLabsVoiceId?: string;    // Custom ElevenLabs voice
  openaiModel?: string;          // OpenAI model (tts-1, tts-1-hd)
}
```

### `TTSLoader` Methods

```typescript
// Speak text with optional provider
await tts.speak(text: string, provider?: string): Promise<boolean>

// Get first available provider
await tts.getProvider(): Promise<TTSProvider | null>

// List all available providers
await tts.listAvailable(): Promise<string[]>
```

## Development

### Project Structure
```
@claude-code/tts/
├── src/
│   ├── index.ts              # Main exports
│   ├── loader.ts             # TTS loader class
│   ├── hooks.ts              # Claude Code integration
│   ├── types.ts              # TypeScript types
│   └── providers/
│       ├── base.ts           # Provider interface
│       ├── say.ts            # Local TTS provider
│       ├── elevenlabs.ts     # ElevenLabs provider
│       └── openai.ts         # OpenAI provider
├── bin/
│   ├── cli.ts                # CLI interface
│   └── install.ts            # Auto-installation
└── dist/                     # Compiled output
```

### Building

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Test locally
npm link
claude-tts speak "Testing local build"
```

### Adding Custom Providers

```typescript
import { BaseTTSProvider, TTSConfig } from '@claude-code/tts';

class CustomProvider extends BaseTTSProvider {
  readonly name = 'custom';
  
  async isAvailable(): Promise<boolean> {
    // Check if provider is available
    return true;
  }
  
  async speak(text: string): Promise<boolean> {
    // Implement TTS logic
    console.log(`Speaking: ${text}`);
    return true;
  }
}

// Use with loader
const tts = loadTTS();
tts.providers.set('custom', new CustomProvider({}));
```

## Troubleshooting

### No Audio Output
- **macOS**: Check System Preferences → Security & Privacy → Privacy → Speech Recognition
- **Linux**: Install `espeak`: `sudo apt-get install espeak`
- **Windows**: Ensure PowerShell execution policy allows scripts

### Provider Not Available
```bash
# Debug provider status
claude-tts list

# Test specific provider
claude-tts speak "test" --provider say
```

### API Key Issues
- Verify environment variables are set: `echo $ELEVENLABS_API_KEY`
- Check `.env` file is in project root
- Ensure API keys have sufficient credits/quota

### Claude Code Integration
- Verify `.claude/settings.json` contains the hook
- Run `claude-tts-install` to reinstall hook
- Check Claude Code logs for hook execution errors

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Build: `npm run build`
5. Test: `npm test`
6. Submit pull request

---

**Built for seamless integration with [Claude Code](https://www.anthropic.com/claude/code)**