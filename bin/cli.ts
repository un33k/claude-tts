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
    
    // If no specific provider requested, announce which one will be used
    if (!options.provider) {
      const provider = await tts.getProvider();
      if (provider) {
        console.log(chalk.blue(`Using ${provider.name} provider...`));
      }
    }
    
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
    const config: any = {};
    if (options.gender) {
      config.voiceGender = options.gender;
    }
    if (options.priority) {
      config.priority = options.priority.split(',').map((s: string) => s.trim());
    }
    
    await ttsNotificationHook(config);
  });

// Default action - run as hook
if (process.argv.length === 2) {
  ttsNotificationHook();
} else {
  program.parse();
}