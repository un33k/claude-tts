import { jest } from '@jest/globals';
import { SettingsManager } from '../../installer/settings-manager.js';
import { promises as fs } from 'fs';

// Mock fs promises
jest.mock('fs', () => ({
  promises: {
    readFile: jest.fn(),
    writeFile: jest.fn(),
    mkdir: jest.fn()
  }
}));

// Mock chalk to avoid color codes in tests
jest.mock('chalk', () => ({
  default: {
    green: (str: string) => str,
    yellow: (str: string) => str,
    blue: (str: string) => str,
    red: (str: string) => str
  }
}));

describe('SettingsManager', () => {
  let manager: SettingsManager;
  const mockSettingsPath = '/test/.claude/settings.json';

  beforeEach(() => {
    jest.clearAllMocks();
    manager = new SettingsManager(mockSettingsPath);
  });

  describe('loadSettings', () => {
    it('should load existing settings', async () => {
      const mockSettings = { hooks: { Notification: [] } };
      (fs.readFile as jest.Mock).mockResolvedValueOnce(JSON.stringify(mockSettings));

      const settings = await manager.loadSettings();

      expect(settings).toEqual(mockSettings);
      expect(fs.readFile).toHaveBeenCalledWith(mockSettingsPath, 'utf8');
    });

    it('should return empty object when file does not exist', async () => {
      (fs.readFile as jest.Mock).mockRejectedValueOnce(new Error('ENOENT'));

      const settings = await manager.loadSettings();

      expect(settings).toEqual({});
    });
  });

  describe('installHooks', () => {
    it('should install new hooks when none exist', async () => {
      (fs.readFile as jest.Mock).mockRejectedValueOnce(new Error('ENOENT'));
      (fs.mkdir as jest.Mock).mockResolvedValueOnce(undefined);
      (fs.writeFile as jest.Mock).mockResolvedValueOnce(undefined);

      await manager.installHooks('/test/hooks');

      expect(fs.writeFile).toHaveBeenCalled();
      const savedSettings = JSON.parse((fs.writeFile as jest.Mock).mock.calls[0][1]);
      expect(savedSettings.hooks).toBeDefined();
      expect(savedSettings.hooks.PreToolUse).toBeDefined();
      expect(savedSettings.hooks.Notification).toBeDefined();
    });

    it('should not duplicate existing STTS hooks', async () => {
      const existingSettings = {
        hooks: {
          Notification: [{
            matcher: '',
            hooks: [{
              type: 'command',
              command: 'node /test/stts/dist/hooks/notification.js'
            }]
          }]
        }
      };
      (fs.readFile as jest.Mock).mockResolvedValueOnce(JSON.stringify(existingSettings));

      const consoleSpy = jest.spyOn(console, 'log');
      await manager.installHooks('/test/hooks');

      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('already installed'));
    });

    it('should preserve non-STTS hooks', async () => {
      const existingSettings = {
        hooks: {
          Notification: [{
            matcher: '',
            hooks: [{
              type: 'command',
              command: 'other-command'
            }]
          }]
        }
      };
      (fs.readFile as jest.Mock).mockResolvedValueOnce(JSON.stringify(existingSettings));
      (fs.writeFile as jest.Mock).mockResolvedValueOnce(undefined);

      await manager.installHooks('/test/hooks');

      const savedSettings = JSON.parse((fs.writeFile as jest.Mock).mock.calls[0][1]);
      expect(savedSettings.hooks.Notification).toHaveLength(2);
      expect(savedSettings.hooks.Notification[0].hooks[0].command).toBe('other-command');
    });
  });

  describe('removeHooks', () => {
    it('should remove only STTS hooks', async () => {
      const settings = {
        hooks: {
          Notification: [
            {
              matcher: '',
              hooks: [{
                type: 'command',
                command: 'node /test/stts/dist/hooks/notification.js'
              }]
            },
            {
              matcher: '',
              hooks: [{
                type: 'command',
                command: 'other-command'
              }]
            }
          ]
        }
      };
      (fs.readFile as jest.Mock).mockResolvedValueOnce(JSON.stringify(settings));
      (fs.writeFile as jest.Mock).mockResolvedValueOnce(undefined);

      await manager.removeHooks();

      const savedSettings = JSON.parse((fs.writeFile as jest.Mock).mock.calls[0][1]);
      expect(savedSettings.hooks.Notification).toHaveLength(1);
      expect(savedSettings.hooks.Notification[0].hooks[0].command).toBe('other-command');
    });

    it('should remove empty hook types after removing STTS hooks', async () => {
      const settings = {
        hooks: {
          Notification: [{
            matcher: '',
            hooks: [{
              type: 'command',
              command: 'node /test/stts/dist/hooks/notification.js'
            }]
          }]
        }
      };
      (fs.readFile as jest.Mock).mockResolvedValueOnce(JSON.stringify(settings));
      (fs.writeFile as jest.Mock).mockResolvedValueOnce(undefined);

      await manager.removeHooks();

      const savedSettings = JSON.parse((fs.writeFile as jest.Mock).mock.calls[0][1]);
      expect(savedSettings.hooks.Notification).toBeUndefined();
    });

    it('should handle no hooks to remove', async () => {
      const settings = { hooks: {} };
      (fs.readFile as jest.Mock).mockResolvedValueOnce(JSON.stringify(settings));

      const consoleSpy = jest.spyOn(console, 'log');
      await manager.removeHooks();

      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('No STTS hooks found'));
      expect(fs.writeFile).not.toHaveBeenCalled();
    });
  });
});