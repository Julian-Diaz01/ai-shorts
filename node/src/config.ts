import * as fs from 'fs-extra';
import * as path from 'path';

interface Config {
  script: {
    topic: string;
    style: string;
    duration_seconds: number | "auto";
    hook_duration: number;
    development_duration: number;
    climax_duration: number;
    max_words_per_scene: number;
  };
  tts: {
    provider: string;
    voice: string;
    rate: string;
    volume: string;
    pitch: string;
    available_voices: {
      male: string[];
      female: string[];
    };
    speed_presets: {
      very_slow: string;
      slow: string;
      normal: string;
      fast: string;
      very_fast: string;
    };
  };
  video: {
    background_video: string;
    resolution: {
      width: number;
      height: number;
    };
    fps: number;
    format: string;
    codec: string;
    audio_codec: string;
    crf: number;
    preset: string;
  };
  llm: {
    model: string;
    temperature: number;
    max_tokens: number;
    use_gpu: boolean;
  };
  output: {
    directory: string;
    script_file: string;
    audio_file: string;
    background_file: string;
    final_video: string;
  };
  text_overlay: {
    enabled: boolean;
    font: string;
    font_size: number;
    font_color: string;
    position: string;
    background_color: string;
    border_width: number;
  };
}

let cachedConfig: Config | null = null;

export function loadConfig(): Config {
  if (cachedConfig) {
    return cachedConfig;
  }

  try {
    // Try multiple possible config locations
    const possiblePaths = [
      path.join(__dirname, '../../config.json'),
      path.join(process.cwd(), 'config.json'),
      'config.json',
    ];

    for (const configPath of possiblePaths) {
      if (fs.existsSync(configPath)) {
        const configData = fs.readFileSync(configPath, 'utf-8');
        cachedConfig = JSON.parse(configData);
        console.log(`✅ Config loaded from: ${configPath}`);
        return cachedConfig!;
      }
    }

    // Default configuration if file not found
    console.warn('⚠️  config.json not found, using default configuration');
    cachedConfig = getDefaultConfig();
    return cachedConfig;
  } catch (error) {
    console.error('❌ Error loading config:', error);
    return getDefaultConfig();
  }
}

function getDefaultConfig(): Config {
  return {
    script: {
      topic: "interesting life stories from Reddit",
      style: "engaging, dramatic storytelling",
      duration_seconds: "auto",
      hook_duration: 8,
      development_duration: 10,
      climax_duration: 12,
      max_words_per_scene: 50
    },
    tts: {
      provider: "edge-tts",
      voice: "en-US-ChristopherNeural",
      rate: "+0%",
      volume: "+0%",
      pitch: "+0Hz",
      available_voices: {
        male: ["en-US-ChristopherNeural", "en-US-EricNeural", "en-US-GuyNeural", "en-US-RogerNeural"],
        female: ["en-US-JennyNeural", "en-US-AriaNeural", "en-US-MichelleNeural"]
      },
      speed_presets: {
        very_slow: "-50%",
        slow: "-25%",
        normal: "+0%",
        fast: "+25%",
        very_fast: "+50%"
      }
    },
    video: {
      background_video: "minecraft_runner.mp4",
      resolution: {
        width: 1080,
        height: 1920
      },
      fps: 30,
      format: "mp4",
      codec: "libx264",
      audio_codec: "aac",
      crf: 23,
      preset: "fast"
    },
    llm: {
      model: "llama3.2",
      temperature: 0.8,
      max_tokens: 500,
      use_gpu: true
    },
    output: {
      directory: "./output",
      script_file: "script.json",
      audio_file: "speech_all.wav",
      background_file: "background.mp4",
      final_video: "short.mp4"
    },
    text_overlay: {
      enabled: false,
      font: "arial.ttf",
      font_size: 48,
      font_color: "white",
      position: "bottom",
      background_color: "black@0.7",
      border_width: 5
    }
  };
}

export function reloadConfig(): Config {
  cachedConfig = null;
  return loadConfig();
}

export function getConfig(): Config {
  return loadConfig();
}

export type { Config };

