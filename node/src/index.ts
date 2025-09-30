import { spawn } from 'child_process';
import * as fs from 'fs-extra';
import * as path from 'path';

class PythonOrchestrator {
  private pythonPath: string;
  private outputPath: string;

  constructor() {
    this.pythonPath = path.join(__dirname, '../../python');
    this.outputPath = path.join(__dirname, '../../output');
    
    // Ensure output directory exists
    fs.ensureDirSync(this.outputPath);
  }

  /**
   * Execute a Python script and return the result
   */
  async executePythonScript(scriptName: string, args: string[] = []): Promise<string> {
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(this.pythonPath, scriptName);
      
      console.log(`Executing Python script: ${scriptName}`);
      console.log(`Arguments: ${args.join(' ')}`);

      const pythonProcess = spawn('python', [scriptPath, ...args], {
        cwd: this.pythonPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          console.log('Python script executed successfully');
          resolve(stdout.trim());
        } else {
          console.error(`Python script failed with code ${code}`);
          console.error('Error output:', stderr);
          reject(new Error(`Python script failed: ${stderr}`));
        }
      });

      pythonProcess.on('error', (error) => {
        console.error('Failed to start Python process:', error);
        reject(error);
      });
    });
  }

  /**
   * Generate TTS audio from text
   */
  async generateTTS(text: string, outputFileName: string): Promise<string> {
    const outputPath = path.join(this.outputPath, outputFileName);
    return this.executePythonScript('tts_generator.py', [text, outputPath]);
  }

  /**
   * Process audio with ffmpeg
   */
  async processAudio(inputFile: string, outputFile: string): Promise<string> {
    const inputPath = path.join(this.outputPath, inputFile);
    const outputPath = path.join(this.outputPath, outputFile);
    return this.executePythonScript('audio_processor.py', [inputPath, outputPath]);
  }
}

// Example usage
async function main() {
  const orchestrator = new PythonOrchestrator();

  try {
    console.log('Starting AI Short Video Pipeline...');
    
    // Example: Generate TTS
    const text = "Hello, this is a test of the TTS system!";
    const ttsResult = await orchestrator.generateTTS(text, 'test_audio.wav');
    console.log('TTS Result:', ttsResult);

    // Example: Process the audio
    const processResult = await orchestrator.processAudio('test_audio.wav', 'processed_audio.wav');
    console.log('Processing Result:', processResult);

    console.log('Pipeline completed successfully!');
  } catch (error) {
    console.error('Pipeline failed:', error);
  }
}

// Run if this file is executed directly
if (require.main === module) {
  main();
}

export { PythonOrchestrator };
