#!/usr/bin/env python3

import sys
import os
import json
import asyncio
import edge_tts
from pathlib import Path
import subprocess
import ffmpeg

def load_config(config_path: str = "../config.json") -> dict:
    try:
        # Try to find config in multiple locations
        possible_paths = [
            config_path,
            os.path.join(os.path.dirname(__file__), "..", "config.json"),
            "config.json",
            "../config.json"
        ]
        
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                with open(abs_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Return default config if file not found
        print("Warning: config.json not found, using default settings")
        return {
            "tts": {
                "voice": "en-US-ChristopherNeural",
                "rate": "+0%",
                "volume": "+0%",
                "pitch": "+0Hz"
            }
        }
    except Exception as e:
        print(f"Error loading config: {e}")
        return {
            "tts": {
                "voice": "en-US-ChristopherNeural",
                "rate": "+0%",
                "volume": "+0%",
                "pitch": "+0Hz"
            }
        }

def load_script_json(script_path: str) -> dict:
    """
    Load and parse the script JSON file
    
    Args:
        script_path: Path to the script.json file
        
    Returns:
        Parsed script data
    """
    try:
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script file not found: {script_path}")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        
        return script_data
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in script file: {str(e)}")
    except Exception as e:
        raise Exception(f"Error loading script: {str(e)}")

async def synthesize_scene_text(text: str, output_path: str, scene_index: int, 
                                voice: str = "en-US-ChristopherNeural",
                                rate: str = "+0%", volume: str = "+0%", pitch: str = "+0Hz") -> str:
    """
    Synthesize speech for a single scene using Edge TTS
    
    Args:
        text: Text to synthesize
        output_path: Path for output audio file
        scene_index: Index of the scene (for logging)
        voice: Voice to use (default: en-US-ChristopherNeural - natural male voice)
        rate: Speech rate (e.g., "-50%" to "+50%")
        volume: Speech volume (e.g., "-50%" to "+50%")
        pitch: Speech pitch (e.g., "-50Hz" to "+50Hz")
        
    Available high-quality voices:
        - en-US-ChristopherNeural (Male, friendly)
        - en-US-EricNeural (Male, professional)
        - en-US-GuyNeural (Male, casual)
        - en-US-RogerNeural (Male, energetic)
        - en-US-JennyNeural (Female, friendly)
        - en-US-AriaNeural (Female, professional)
        - en-US-MichelleNeural (Female, warm)
        
    Returns:
        Success message
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Generate speech using Edge TTS with custom parameters
        print(f"  Generating audio for scene {scene_index} with voice: {voice}, rate: {rate}")
        
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
        await communicate.save(output_path)
        
        return f"Scene {scene_index} synthesized: {output_path}"
        
    except Exception as e:
        return f"Error synthesizing scene {scene_index}: {str(e)}"


def get_audio_duration(audio_path: str) -> float:
    """
    Get the duration of an audio file using FFprobe
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Duration in seconds
    """
    try:
        probe = ffmpeg.probe(audio_path)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        
        if audio_stream:
            return float(audio_stream['duration'])
        else:
            return 0.0
    except Exception as e:
        print(f"Warning: Could not get duration for {audio_path}: {e}")
        return 0.0


def combine_audio_files(audio_files: list, output_path: str) -> str:
    """
    Combine multiple audio files into one using FFmpeg
    
    Args:
        audio_files: List of audio file paths
        output_path: Path for combined output file
        
    Returns:
        Success message
    """
    try:
        if not audio_files:
            return "No audio files to combine"
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Create FFmpeg command to concatenate audio files
        cmd = ['ffmpeg', '-y']  # -y to overwrite output file
        
        # Add input files
        for audio_file in audio_files:
            if os.path.exists(audio_file):
                cmd.extend(['-i', audio_file])
        
        # Add filter for concatenation
        filter_complex = 'concat=n=' + str(len(audio_files)) + ':v=0:a=1[out]'
        cmd.extend(['-filter_complex', filter_complex])
        cmd.extend(['-map', '[out]'])
        
        # Add output file
        cmd.append(output_path)
        
        # Run FFmpeg command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Audio files combined successfully: {output_path}"
        else:
            return f"FFmpeg error: {result.stderr}"
        
    except Exception as e:
        return f"Error combining audio files: {str(e)}"

async def synthesize_script_async(script_path: str, output_path: str, 
                                 voice: str = None, rate: str = None,
                                 volume: str = None, pitch: str = None) -> str:
    """
    Synthesize speech for entire script using Edge TTS (async)
    
    Args:
        script_path: Path to script.json
        output_path: Path for final combined audio file
        voice: Voice to use (overrides config if provided)
        rate: Speech rate (overrides config if provided)
        volume: Speech volume (overrides config if provided)
        pitch: Speech pitch (overrides config if provided)
        
    Returns:
        Success message
    """
    try:
        # Load configuration
        config = load_config()
        tts_config = config.get('tts', {})
        
        # Use provided parameters or fall back to config
        voice = voice or tts_config.get('voice', 'en-US-ChristopherNeural')
        rate = rate or tts_config.get('rate', '+0%')
        volume = volume or tts_config.get('volume', '+0%')
        pitch = pitch or tts_config.get('pitch', '+0Hz')
        
        # Load script data
        print("Loading script data...")
        script_data = load_script_json(script_path)
        scenes = script_data['scenes']
        
        print(f"Script loaded: {script_data['title']}")
        print(f"Scenes to synthesize: {len(scenes)}")
        print(f"\nTTS Settings:")
        print(f"  Voice: {voice}")
        print(f"  Speed: {rate}")
        print(f"  Volume: {volume}")
        print(f"  Pitch: {pitch}")
        
        # Synthesize each scene and measure actual durations
        scene_audio_files = []
        updated_scenes = []
        current_time = 0.0
        
        for i, scene in enumerate(scenes):
            print(f"Synthesizing scene {i + 1}/{len(scenes)}...")
            
            # Create individual scene audio file
            scene_audio_path = os.path.join(os.path.dirname(output_path), f'scene_{i + 1}.mp3')
            
            # Synthesize scene text
            result = await synthesize_scene_text(scene['voice'], scene_audio_path, i + 1, 
                                                voice, rate, volume, pitch)
            print(f"  {result}")
            
            if os.path.exists(scene_audio_path):
                scene_audio_files.append(scene_audio_path)
                
                # Measure actual duration of generated audio
                actual_duration = get_audio_duration(scene_audio_path)
                
                # Update scene with actual timing
                updated_scene = scene.copy()
                updated_scene['start'] = round(current_time, 2)
                updated_scene['end'] = round(current_time + actual_duration, 2)
                updated_scenes.append(updated_scene)
                
                print(f"  Actual duration: {actual_duration:.2f}s (start: {updated_scene['start']:.2f}s, end: {updated_scene['end']:.2f}s)")
                
                # Update current time for next scene
                current_time += actual_duration
            else:
                # If audio file doesn't exist, keep original timing
                updated_scenes.append(scene)
                print(f"  Warning: Audio file not found, keeping original timing")
        
        # Update script data with actual timings
        script_data['scenes'] = updated_scenes
        script_data['duration_seconds'] = round(current_time, 2)
        
        # Save updated script with actual timings
        script_path_updated = script_path.replace('.json', '_updated.json')
        with open(script_path_updated, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        
        print(f"Updated script with actual timings saved to: {script_path_updated}")
        print(f"Total actual duration: {current_time:.2f} seconds")
        
        # Combine all scene audio files
        print("Combining audio files...")
        combine_result = combine_audio_files(scene_audio_files, output_path)
        print(combine_result)
        
        # Clean up individual scene files
        for scene_file in scene_audio_files:
            try:
                os.remove(scene_file)
            except:
                pass  # Ignore cleanup errors
        
        return f"Speech synthesis completed: {output_path}"
        
    except Exception as e:
        return f"Error synthesizing script: {str(e)}"

def synthesize_script(script_path: str, output_path: str, 
                     voice: str = None, rate: str = None,
                     volume: str = None, pitch: str = None) -> str:
    """
    Synchronous wrapper for synthesize_script_async
    """
    return asyncio.run(synthesize_script_async(script_path, output_path, voice, rate, volume, pitch))

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python synth.py [script_path] [output_path] [voice] [rate]")
        print("Example: python synth.py ../output/script.json ../output/speech_all.wav en-US-ChristopherNeural +25%")
        print("\nNote: If parameters are not provided, they will be read from config.json")
        print("\nAvailable voices:")
        print("  Male: en-US-ChristopherNeural, en-US-EricNeural, en-US-GuyNeural, en-US-RogerNeural")
        print("  Female: en-US-JennyNeural, en-US-AriaNeural, en-US-MichelleNeural")
        print("\nSpeed examples: -50% (very slow), -25% (slow), +0% (normal), +25% (fast), +50% (very fast)")
        sys.exit(1)
    
    # Default paths
    script_path = sys.argv[1] if len(sys.argv) > 1 else "../output/script.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "../output/speech_all.wav"
    voice = sys.argv[3] if len(sys.argv) > 3 else None
    rate = sys.argv[4] if len(sys.argv) > 4 else None
    
    # Convert relative paths to absolute paths
    script_path = os.path.abspath(script_path)
    output_path = os.path.abspath(output_path)
    
    result = synthesize_script(script_path, output_path, voice, rate)
    print(result)

if __name__ == "__main__":
    main()
