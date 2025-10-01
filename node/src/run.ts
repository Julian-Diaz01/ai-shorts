import { PythonOrchestrator } from './index';
import { YouTubeShortGenerator } from './generate';
import { loadConfig } from './config';
import * as path from 'path';

class FullPipeline {
  private orchestrator: PythonOrchestrator;
  private generator: YouTubeShortGenerator;
  private config: ReturnType<typeof loadConfig>;

  constructor() {
    this.config = loadConfig();
    this.orchestrator = new PythonOrchestrator();
    this.generator = new YouTubeShortGenerator();
  }

  /**
   * Run the complete YouTube Short generation pipeline
   */
  async runFullPipeline(inputVideo?: string): Promise<void> {
    // Use config value if no video specified
    if (!inputVideo) {
      inputVideo = this.config.video.background_video;
    }
    try {
      console.log('🎬 Starting YouTube Short Generation Pipeline...\n');
      console.log('⚙️  Configuration:');
      console.log(`   📝 Topic: ${this.config.script.topic}`);
      console.log(`   🎤 Voice: ${this.config.tts.voice}`);
      console.log(`   ⚡ Speed: ${this.config.tts.rate}`);
      console.log(`   🎥 Background: ${inputVideo}`);
      console.log(`   ⏱️  Duration: ${this.config.script.duration_seconds === "auto" ? "auto (based on audio)" : this.config.script.duration_seconds + "s"}\n`);

      // Step 1: Generate script using local LLM
      console.log('📝 Step 1: Generating script with local LLM...');
      await this.generator.initializeModel();
      const script = await this.generator.generateScript();
      await this.generator.saveScript(script);
      await this.generator.cleanup();
      console.log('✅ Script generated successfully!\n');

      // Step 2: Synthesize speech from script
      console.log('🎤 Step 2: Synthesizing speech...');
      const synthResult = await this.orchestrator.executePythonScript('synth.py', ['../output/script.json', '../output/speech_all.wav']);
      console.log('Speech synthesis result:', synthResult);
      console.log('✅ Speech synthesis completed!\n');

      // Step 3: Get audio duration and prepare background video to match
      console.log('🎥 Step 3: Getting audio duration and preparing background video...');
      const audioDurationResult = await this.orchestrator.executePythonScript('audio_utils.py', ['../output/speech_all.wav']);
      console.log('Audio duration result:', audioDurationResult);
      
      // Extract duration from the result (assuming it's in the format "Duration: X.XX seconds")
      const durationMatch = audioDurationResult.match(/Duration: ([\d.]+) seconds/);
      const audioDuration = durationMatch ? parseFloat(durationMatch[1]) : 30.0;
      console.log(`Detected audio duration: ${audioDuration} seconds`);
      
      const videoResult = await this.orchestrator.prepareBackgroundVideo(inputVideo, 'background.mp4', audioDuration);
      console.log('Video preparation result:', videoResult);
      console.log('✅ Background video prepared!\n');

      // Step 4: Assemble final video
      console.log('🎬 Step 4: Assembling final video...');
      const assembleResult = await this.orchestrator.executePythonScript('assemble.py', ['../output/script.json', '../output/background.mp4', '../output/speech_all.wav', '../output/short.mp4']);
      console.log('Video assembly result:', assembleResult);
      console.log('✅ Final video assembled!\n');

      console.log('🎉 Pipeline completed successfully!');
      console.log('📁 Output files:');
      console.log('   - /output/script.json (Script)');
      console.log('   - /output/speech_all.wav (Audio)');
      console.log('   - /output/background.mp4 (Background video)');
      console.log('   - /output/short.mp4 (Final YouTube Short)');

    } catch (error) {
      console.error('❌ Pipeline failed:', error);
      throw error;
    }
  }

  /**
   * Run individual pipeline steps
   */
  async runStep(step: string, inputVideo?: string): Promise<void> {
    switch (step) {
      case 'generate':
        console.log('📝 Generating script...');
        await this.generator.initializeModel();
        const script = await this.generator.generateScript();
        await this.generator.saveScript(script);
        await this.generator.cleanup();
        console.log('✅ Script generated!');
        break;

      case 'synth':
        console.log('🎤 Synthesizing speech...');
        const synthResult = await this.orchestrator.executePythonScript('synth.py');
        console.log('✅ Speech synthesized!');
        break;

      case 'prepare-video':
        if (!inputVideo) {
          throw new Error('Input video path required for prepare-video step');
        }
        console.log('🎥 Preparing background video...');
        const videoResult = await this.orchestrator.prepareBackgroundVideo(inputVideo, 'background.mp4', 30);
        console.log('✅ Background video prepared!');
        break;

      case 'assemble':
        console.log('🎬 Assembling final video...');
        const assembleResult = await this.orchestrator.executePythonScript('assemble.py', ['../output/script.json', '../output/background.mp4', '../output/speech_all.wav', '../output/short.mp4']);
        console.log('✅ Final video assembled!');
        break;

      default:
        throw new Error(`Unknown step: ${step}. Available steps: generate, synth, prepare-video, assemble`);
    }
  }
}

// Main execution function
async function main() {
  const pipeline = new FullPipeline();
  
  // Parse command line arguments
  const args = process.argv.slice(2);
  const step = args[0];
  const inputVideo = args[1];

  try {
    if (step) {
      // Run individual step
      await pipeline.runStep(step, inputVideo);
    } else {
      // Run full pipeline
      await pipeline.runFullPipeline(inputVideo);
    }
  } catch (error) {
    console.error('❌ Pipeline failed:', error);
    process.exit(1);
  }
}

// Run if this file is executed directly
if (require.main === module) {
  main();
}

export { FullPipeline };
