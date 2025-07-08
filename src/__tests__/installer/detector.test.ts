import { jest } from '@jest/globals';
import { ToolDetector } from '../../installer/detector.js';

// Mock the which module
jest.mock('which', () => ({
  default: jest.fn()
}));

// Mock fs promises
jest.mock('fs', () => ({
  promises: {
    access: jest.fn()
  }
}));

// Mock os
jest.mock('os', () => ({
  homedir: jest.fn(() => '/home/test')
}));

describe('ToolDetector', () => {
  let detector: ToolDetector;
  let whichMock: jest.Mock;
  let fsAccessMock: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    detector = new ToolDetector();
    
    // Get mocked functions
    whichMock = require('which').default;
    fsAccessMock = require('fs').promises.access;
  });

  describe('detect', () => {
    it('should detect claude-code when executable exists', async () => {
      whichMock.mockResolvedValueOnce('/usr/local/bin/claude-code');
      
      const results = await detector.detect('claude-code');
      
      expect(results).toHaveLength(1);
      expect(results[0]).toMatchObject({
        name: 'Claude Code',
        executable: 'claude-code',
        detected: true
      });
    });

    it('should not detect claude-code when executable is missing', async () => {
      whichMock.mockRejectedValueOnce(new Error('not found'));
      
      const results = await detector.detect('claude-code');
      
      expect(results).toHaveLength(1);
      expect(results[0].detected).toBe(false);
    });

    it('should fall back to claude when claude-code is not found', async () => {
      whichMock
        .mockRejectedValueOnce(new Error('not found')) // claude-code
        .mockResolvedValueOnce('/usr/local/bin/claude'); // claude fallback
      
      const results = await detector.detect('claude-code');
      
      expect(results[0].detected).toBe(true);
    });

    it('should detect all tools when no specific tool is provided', async () => {
      whichMock
        .mockResolvedValueOnce('/usr/local/bin/claude-code')
        .mockResolvedValueOnce('/usr/local/bin/claude');
      
      const results = await detector.detect();
      
      expect(results.length).toBeGreaterThan(1);
      expect(results.every(r => r.detected)).toBe(true);
    });
  });

  describe('getSettingsPath', () => {
    it('should return settings path when file exists', async () => {
      fsAccessMock.mockResolvedValueOnce(undefined);
      
      const path = await detector.getSettingsPath('claude-code');
      
      expect(path).toBe('/home/test/.claude/settings.json');
    });

    it('should return null when settings file does not exist', async () => {
      fsAccessMock.mockRejectedValue(new Error('ENOENT'));
      
      const path = await detector.getSettingsPath('claude-code');
      
      expect(path).toBeNull();
    });

    it('should return null for unknown tool', async () => {
      const path = await detector.getSettingsPath('unknown-tool');
      
      expect(path).toBeNull();
    });
  });
});