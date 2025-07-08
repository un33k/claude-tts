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
    
    // Test TTS functionality
    console.log(chalk.blue('\n📢 Testing TTS functionality...'));
    try {
      const { loadTTS } = await import('../src/index.js');
      const tts = loadTTS();
      const providers = await tts.listAvailable();
      console.log(chalk.green(`✓ Found ${providers.length} available TTS providers: ${providers.join(', ')}`));
      
      if (providers.length > 0) {
        console.log(chalk.blue('🔊 Speaking test message...'));
        const provider = await tts.getProvider();
        const providerName = provider ? provider.name : 'unknown';
        const success = await tts.speak(`Claude TTS installed successfully using ${providerName} provider!`);
        if (success) {
          console.log(chalk.green(`✓ TTS test successful using ${providerName} provider!`));
        } else {
          console.log(chalk.yellow('⚠ TTS test failed - check your audio settings'));
        }
      }
    } catch (error) {
      console.log(chalk.yellow('⚠ Could not test TTS functionality'));
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