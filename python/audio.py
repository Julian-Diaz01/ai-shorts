import os
import sys
import json
import asyncio
import edge_tts
import ffmpeg
from typing import Dict, List, Any


def load_config() -> Dict[str, Any]:
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")
        return {}


def get_audio_duration(input_path: str) -> float:
    try:
        probe = ffmpeg.probe(input_path)
        duration = float(probe['streams'][0]['duration'])
        return duration
    except Exception as e:
        raise Exception(f"Error getting audio duration: {str(e)}")


def convert_rate_to_prosody(rate: str) -> str:
    if rate.endswith('%'):
        try:
            percentage = int(rate.replace('%', '').replace('+', ''))
            if percentage >= 50:
                return "x-fast"
            elif percentage >= 25:
                return "fast"
            elif percentage >= 0:
                return "medium"
            elif percentage >= -25:
                return "slow"
            else:
                return "x-slow"
        except:
            return "medium"
    
    # Already a named rate
    return rate


async def synthesize_text(text: str, output_path: str, voice: str = "en-US-ChristopherNeural", 
                         rate: str = "medium", volume: str = "+0%", pitch: str = "+0Hz") -> None:
    try:
        # Convert rate to prosody format
        prosody_rate = convert_rate_to_prosody(rate)
        
        # Create TTS communication
        communicate = edge_tts.Communicate(text, voice, rate=prosody_rate, volume=volume, pitch=pitch)
        
        # Save to file
        await communicate.save(output_path)
        
    except Exception as e:
        raise Exception(f"Error synthesizing text: {str(e)}")


def synthesize_scene_text(scene_text: str, output_path: str) -> None:
    config = load_config()
    tts_config = config.get('tts', {})
    
    voice = tts_config.get('voice', 'en-US-ChristopherNeural')
    rate = tts_config.get('rate', 'medium')
    volume = tts_config.get('volume', '+0%')
    pitch = tts_config.get('pitch', '+0Hz')
    
    print(f"Synthesizing scene text...")
    
    # Run async synthesis
    asyncio.run(synthesize_text(scene_text, output_path, voice, rate, volume, pitch))


def combine_audio_files(audio_files: List[str], output_path: str) -> None:
    try:
        if len(audio_files) == 1:
            # Just copy the single file
            import shutil
            shutil.copy2(audio_files[0], output_path)
            return
        
        # Create input streams
        inputs = [ffmpeg.input(file) for file in audio_files]
        
        # Concatenate audio streams
        output = ffmpeg.concat(*inputs, v=0, a=1)
        
        # Run conversion
        ffmpeg.run(output, overwrite_output=True, quiet=True)
        
    except Exception as e:
        raise Exception(f"Error combining audio files: {str(e)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python audio.py <command> [args...]")
        print("Commands:")
        print("  duration <audio_file> - Get audio duration")
        print("  synthesize <text> <output> - Synthesize text to speech")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "duration":
        if len(sys.argv) < 3:
            print("Usage: python audio.py duration <audio_file>")
            sys.exit(1)
        
        audio_file = sys.argv[2]
        try:
            duration = get_audio_duration(audio_file)
            print(f"Duration: {duration:.2f} seconds")
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    
    elif command == "synthesize":
        if len(sys.argv) < 4:
            print("Usage: python audio.py synthesize <text> <output>")
            sys.exit(1)
        
        text = sys.argv[2]
        output = sys.argv[3]
        try:
            synthesize_scene_text(text, output)
            print(f"Audio synthesized: {output}")
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
