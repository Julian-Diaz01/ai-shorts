import * as fs from 'fs-extra';
import * as path from 'path';
import { loadConfig, Config } from './config';

interface Scene {
  id: string;
  name: string;
  description: string;
  topic: string;
  style: string;
  hook_duration: number;
  development_duration: number;
  climax_duration: number;
  max_words_per_scene: number;
  voice: string;
  rate: string;
  example_script: YouTubeShortScript;
}

interface ScenesData {
  scenes: Scene[];
  default_scene: string;
}

interface ScriptScene {
  start: number;
  end: number;
  voice: string;
  overlay: string;
}

interface YouTubeShortScript {
  title: string;
  duration_seconds: number;
  scenes: ScriptScene[];
}

class YouTubeShortGenerator {
  private model: any = null;
  private outputPath: string;
  private config: Config;
  private scenesData: ScenesData;

  constructor() {
    this.config = loadConfig();
    this.outputPath = path.join(__dirname, '../../output');
    // Ensure output directory exists
    fs.ensureDirSync(this.outputPath);
    
    // Load scenes data
    this.scenesData = this.loadScenesData();
  }

  /**
   * Load scenes data from scenes.json
   */
  private loadScenesData(): ScenesData {
    try {
      const scenesPath = path.join(__dirname, '../../scenes.json');
      if (fs.existsSync(scenesPath)) {
        const scenesData = fs.readFileSync(scenesPath, 'utf-8');
        return JSON.parse(scenesData);
      }
    } catch (error) {
      console.warn('Could not load scenes.json:', error);
    }
    
    throw new Error('scenes.json file is required but not found');
  }

  /**
   * Initialize the local LLM
   */
  async initializeModel(): Promise<void> {
    try {
      console.log('Loading local LLM...');
      // For now, skip actual model loading and use mock data
      console.log('Using mock script generation (skipping LLM for faster testing)');
      this.model = { mock: true };
    } catch (error) {
      console.error('Failed to load local LLM:', error);
      throw error;
    }
  }


  /**
   * Generate YouTube Short script using local LLM
   */
  async generateScript(): Promise<YouTubeShortScript> {
    if (!this.model) {
      throw new Error('Model not initialized. Call initializeModel() first.');
    }

    try {
      console.log('Generating YouTube Short script...');
      
      // Get the default scene or find scene by config
      const defaultScene = this.scenesData.scenes.find(scene => scene.id === this.scenesData.default_scene) || this.scenesData.scenes[0];
      
      // Use the example script from the scene
      const script: YouTubeShortScript = defaultScene.example_script;

      console.log(`Generated script from scene "${defaultScene.name}":`, script.title);
      this.validateScript(script);
      return script;
    } catch (error) {
      console.error('Error generating script:', error);
      throw error;
    }
  }

  /**
   * Validate the generated script structure
   */
  private validateScript(script: YouTubeShortScript): void {
    if (!script.title || typeof script.title !== 'string') {
      throw new Error('Invalid or missing title');
    }

    // Duration validation is now dynamic - will be validated against actual audio duration
    if (typeof script.duration_seconds !== 'number' || script.duration_seconds <= 0) {
      throw new Error('Duration must be a positive number');
    }

    if (!Array.isArray(script.scenes) || script.scenes.length === 0) {
      throw new Error('Scenes must be a non-empty array');
    }

    // Validate each scene
    script.scenes.forEach((scene, index) => {
      if (typeof scene.start !== 'number' || typeof scene.end !== 'number') {
        throw new Error(`Scene ${index}: start and end must be numbers`);
      }

      if (scene.start < 0 || scene.end > script.duration_seconds || scene.start >= scene.end) {
        throw new Error(`Scene ${index}: invalid timing (start: ${scene.start}, end: ${scene.end}) - must be within 0-${script.duration_seconds} seconds`);
      }

      if (!scene.voice || typeof scene.voice !== 'string') {
        throw new Error(`Scene ${index}: voice must be a non-empty string`);
      }

      if (!scene.overlay || typeof scene.overlay !== 'string') {
        throw new Error(`Scene ${index}: overlay must be a non-empty string`);
      }
    });

    // Check for scene overlaps
    for (let i = 1; i < script.scenes.length; i++) {
      if (script.scenes[i].start < script.scenes[i - 1].end) {
        throw new Error(`Scene ${i} overlaps with previous scene`);
      }
    }
  }

  /**
   * Save the generated script to output directory
   */
  async saveScript(script: YouTubeShortScript): Promise<string> {
    const outputFile = path.join(this.outputPath, 'script.json');
    
    try {
      await fs.writeJson(outputFile, script, { spaces: 2 });
      console.log(`Script saved to: ${outputFile}`);
      return outputFile;
    } catch (error) {
      console.error('Error saving script:', error);
      throw error;
    }
  }

  /**
   * Generate and save a complete YouTube Short script
   */
  async generateAndSave(): Promise<string> {
    try {
      await this.initializeModel();
      const script = await this.generateScript();
      const outputFile = await this.saveScript(script);
      
      console.log('YouTube Short script generated successfully!');
      console.log('Title:', script.title);
      console.log('Duration:', script.duration_seconds, 'seconds');
      console.log('Scenes:', script.scenes.length);
      
      return outputFile;
    } catch (error) {
      console.error('Failed to generate YouTube Short script:', error);
      throw error;
    }
  }

  /**
   * Clean up resources
   */
  async cleanup(): Promise<void> {
    if (this.model) {
      try {
        // Clean up model resources
        if (typeof this.model.dispose === 'function') {
          this.model.dispose();
        }
        console.log('Model closed successfully');
      } catch (error) {
        console.error('Error closing model:', error);
      }
    }
  }
}

// Main execution function
async function main() {
  const generator = new YouTubeShortGenerator();
  
  try {
    const outputFile = await generator.generateAndSave();
    console.log(`\n✅ Success! Script saved to: ${outputFile}`);
  } catch (error) {
    console.error('\n❌ Failed to generate script:', error);
    process.exit(1);
  } finally {
    await generator.cleanup();
  }
}

// Run if this file is executed directly
if (require.main === module) {
  main();
}

export { YouTubeShortGenerator, YouTubeShortScript, Scene };
