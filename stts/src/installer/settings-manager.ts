import { promises as fs } from 'fs';
import { dirname, join } from 'path';
import { ClaudeSettings, HookMatcher } from '../types.js';
import chalk from 'chalk';

export class SettingsManager {
  constructor(private settingsPath: string) {}

  async loadSettings(): Promise<ClaudeSettings> {
    try {
      const content = await fs.readFile(this.settingsPath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      // If file doesn't exist or is invalid, return empty settings
      return {};
    }
  }

  async saveSettings(settings: ClaudeSettings): Promise<void> {
    const dir = dirname(this.settingsPath);
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(this.settingsPath, JSON.stringify(settings, null, 2));
  }

  async installHooks(hookScriptsPath: string): Promise<void> {
    const settings = await this.loadSettings();
    
    // Initialize hooks structure
    if (!settings.hooks) {
      settings.hooks = {};
    }

    // Define all hook types and their corresponding scripts
    const hookTypes = [
      { name: 'PreToolUse', script: 'pre-tool-use.js' },
      { name: 'PostToolUse', script: 'post-tool-use.js' },
      { name: 'Notification', script: 'notification.js' },
      { name: 'Stop', script: 'stop.js' },
      { name: 'SubagentStop', script: 'subagent-stop.js' }
    ];

    let updated = false;

    for (const { name, script } of hookTypes) {
      const scriptPath = join(hookScriptsPath, script);
      const hookEntry: HookMatcher = {
        matcher: '',
        hooks: [{
          type: 'command',
          command: `node ${scriptPath}`
        }]
      };

      // Check if hook already exists
      const hookKey = name as keyof typeof settings.hooks;
      if (!settings.hooks[hookKey]) {
        settings.hooks[hookKey] = [];
      }

      // Check if our hook is already installed
      const existing = settings.hooks[hookKey]!.find(h => 
        h.hooks.some(hook => hook.command.includes(script))
      );

      if (!existing) {
        settings.hooks[hookKey]!.push(hookEntry);
        updated = true;
        console.log(chalk.green(`✓ Installed ${name} hook`));
      } else {
        console.log(chalk.yellow(`⚠ ${name} hook already installed`));
      }
    }

    if (updated) {
      await this.saveSettings(settings);
      console.log(chalk.green(`\n✓ Settings updated: ${this.settingsPath}`));
    } else {
      console.log(chalk.yellow('\n⚠ All hooks already installed'));
    }
  }

  async removeHooks(): Promise<void> {
    const settings = await this.loadSettings();
    
    if (!settings.hooks) {
      console.log(chalk.yellow('No hooks found to remove'));
      return;
    }

    let removed = false;

    // Remove STTS hooks from each hook type
    for (const hookType of Object.keys(settings.hooks)) {
      const hooks = settings.hooks[hookType as keyof typeof settings.hooks];
      if (!hooks) continue;

      const filtered = hooks.filter(h => 
        !h.hooks.some(hook => 
          hook.command.includes('stts/dist/hooks/') ||
          hook.command.includes('@ehaye/stts')
        )
      );

      if (filtered.length < hooks.length) {
        settings.hooks[hookType as keyof typeof settings.hooks] = filtered.length > 0 ? filtered : undefined;
        removed = true;
        console.log(chalk.green(`✓ Removed ${hookType} hook`));
      }
    }

    if (removed) {
      await this.saveSettings(settings);
      console.log(chalk.green(`\n✓ Settings updated: ${this.settingsPath}`));
    } else {
      console.log(chalk.yellow('No STTS hooks found to remove'));
    }
  }
}