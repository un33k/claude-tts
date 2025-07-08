import { spawn } from 'child_process';
import { BaseTTSProvider } from './base.js';
import { TTSConfig } from '../types.js';

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