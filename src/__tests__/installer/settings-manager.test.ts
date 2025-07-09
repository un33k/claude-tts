import { jest } from '@jest/globals';

// Mock fs promises
const mockReadFile = jest.fn() as any;
const mockWriteFile = jest.fn() as any;
const mockMkdir = jest.fn() as any;
jest.mock('fs', () => ({
  promises: {
    readFile: mockReadFile,
    writeFile: mockWriteFile,
    mkdir: mockMkdir
  }
}));

// Mock path
jest.mock('path', () => ({
  dirname: jest.fn(() => '/test'),
  join: jest.fn((...args) => args.join('/'))
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

// Now import the module under test
import { SettingsManager } from '../../installer/settings-manager.js';

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
      mockReadFile.mockResolvedValueOnce(JSON.stringify(mockSettings));

      const settings = await manager.loadSettings();

      expect(settings).toEqual(mockSettings);
      expect(mockReadFile).toHaveBeenCalledWith(mockSettingsPath, 'utf8');
    });

    it('should return empty object when file does not exist', async () => {
      mockReadFile.mockRejectedValueOnce(new Error('ENOENT'));

      const settings = await manager.loadSettings();

      expect(settings).toEqual({});
    });
  });

  describe('installHooks', () => {
    it('should install new hooks when none exist', async () => {
      mockReadFile.mockRejectedValueOnce(new Error('ENOENT'));
      mockMkdir.mockResolvedValueOnce(undefined);
      mockWriteFile.mockResolvedValueOnce(undefined);

      await manager.installHooks('/test/hooks');

      expect(mockWriteFile).toHaveBeenCalled();
      const savedSettings = JSON.parse(mockWriteFile.mock.calls[0][1] as string);
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
      mockReadFile.mockResolvedValueOnce(JSON.stringify(existingSettings));

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
      mockReadFile.mockResolvedValueOnce(JSON.stringify(existingSettings));
      mockWriteFile.mockResolvedValueOnce(undefined);

      await manager.installHooks('/test/hooks');

      const savedSettings = JSON.parse(mockWriteFile.mock.calls[0][1] as string);
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
      mockReadFile.mockResolvedValueOnce(JSON.stringify(settings));
      mockWriteFile.mockResolvedValueOnce(undefined);

      await manager.removeHooks();

      expect(mockWriteFile).toHaveBeenCalled();
      const savedSettings = JSON.parse(mockWriteFile.mock.calls[0][1] as string);
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
      mockReadFile.mockResolvedValueOnce(JSON.stringify(settings));
      mockWriteFile.mockResolvedValueOnce(undefined);

      await manager.removeHooks();

      expect(mockWriteFile).toHaveBeenCalled();
      const savedSettings = JSON.parse(mockWriteFile.mock.calls[0][1] as string);
      expect(savedSettings.hooks.Notification).toBeUndefined();
    });

    it('should handle no hooks to remove', async () => {
      const settings = {}; // No hooks object at all
      mockReadFile.mockResolvedValueOnce(JSON.stringify(settings));

      const consoleSpy = jest.spyOn(console, 'log');
      await manager.removeHooks();

      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('No hooks found to remove'));
      expect(mockWriteFile).not.toHaveBeenCalled();
    });
  });
});