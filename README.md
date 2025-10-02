# AI Short Video Generator

Generate YouTube Shorts using AI script generation, text-to-speech, and video assembly.

## Project Structure

```
ai-short/
├── node/         # TypeScript orchestrator
├── python/       # Python TTS and video processing
└── output/       # Generated videos
```

## Quick Setup

1. Install Node.js and Python
2. Install FFmpeg
3. Run setup scripts:
```bash
cd node && npm install
cd python && pip install -r requirements.txt
```

## Usage

### Generate a complete short:
```bash
cd node
npm run generate    # Create script
npm run synth       # Generate speech
npm run prepare-video  # Prepare background video
npm run assemble    # Create final video
```

### Or run everything at once:
```bash
cd node
npm run full
```

## Features

- Automatic script generation with local LLM
- Natural text-to-speech synthesis 
- Video cropping and preparation for mobile
- Subtitle overlays
- Cross-platform support

## Configuration

Edit `config.json` to customize voices, topics, and video settings.