#!/usr/bin/env python3
"""
Video Assembly Script
Assembles final YouTube Short by combining background video, audio, and subtitles
Uses the new modular approach with separate audio, text, and video modules
"""

import sys
import os
import json
import ffmpeg
from pathlib import Path
from typing import List, Dict, Any

# Import our new modules
from audio import get_audio_duration
from text import create_subtitle_file
from video import add_subtitles_to_video


def load_script_json(script_path: str) -> Dict[str, Any]:
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Error loading script JSON: {str(e)}")


def load_config() -> Dict[str, Any]:
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")
        return {}


def assemble_video_with_subtitles(script_path: str, background_video: str, audio_file: str, output_path: str) -> str:
    try:
        # Check if all required files exist
        required_files = [script_path, background_video, audio_file]
        for file_path in required_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file not found: {file_path}")
        
        # Check for updated script with actual timings first
        script_path_updated = script_path.replace('.json', '_updated.json')
        if os.path.exists(script_path_updated):
            print("Found updated script with actual timings, using that...")
            script_path = script_path_updated
        
        # Load script data
        print("Loading script data...")
        script_data = load_script_json(script_path)
        scenes = script_data['scenes']
        
        # Get actual audio duration instead of script duration
        print("Getting actual audio duration...")
        actual_duration = get_audio_duration(audio_file)
        
        print(f"Script loaded: {script_data['title']}")
        print(f"Script duration: {script_data['duration_seconds']} seconds")
        print(f"Actual audio duration: {actual_duration:.2f} seconds")
        print(f"Scenes: {len(scenes)}")
        
        # Load configuration
        config = load_config()
        text_config = config.get('text_overlay', {})
        subtitle_enabled = text_config.get('enabled', True)
        
        if subtitle_enabled:
            print("Creating ASS subtitle file...")
            
            # Create subtitle file using the text module (ASS format only)
            # Pass the scenes data directly from script.json
            subtitle_path = create_subtitle_file(scenes, output_path.replace('.mp4', '_subtitles'))
            
            print(f"Subtitle file created: {subtitle_path}")
            
            # Create temporary video without subtitles first
            temp_video = output_path.replace('.mp4', '_temp.mp4')
            
            # Combine video and audio
            print("Combining video and audio...")
            video_input = ffmpeg.input(background_video)
            audio_input = ffmpeg.input(audio_file)
            
            output = ffmpeg.output(
                video_input,
                audio_input,
                temp_video,
                vcodec='libx264',
                acodec='aac',
                preset='fast',
                crf=23,
                t=actual_duration,
                shortest=None
            )
            
            # Run the conversion
            print("Rendering video with audio...")
            ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            # Add subtitles using the video module
            print("Adding subtitles...")
            add_subtitles_to_video(temp_video, subtitle_path, output_path)
            
            # Clean up temporary files
            if os.path.exists(temp_video):
                os.remove(temp_video)
            if os.path.exists(subtitle_path):
                os.remove(subtitle_path)
            
            print(f"Video with subtitles assembled: {output_path}")
            
        else:
            print("Subtitles disabled, creating video without subtitles...")
            
            # Combine video and audio directly
            video_input = ffmpeg.input(background_video)
            audio_input = ffmpeg.input(audio_file)
            
            output = ffmpeg.output(
                video_input,
                audio_input,
                output_path,
                vcodec='libx264',
                acodec='aac',
                preset='fast',
                crf=23,
                t=actual_duration,
                shortest=None
            )
            
            # Run the conversion
            print("Rendering final video...")
            ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            print(f"Video assembled: {output_path}")
        
        return output_path
        
    except ffmpeg.Error as e:
        stderr_output = e.stderr.decode('utf-8') if e.stderr else 'No stderr output'
        raise Exception(f"FFmpeg error: {stderr_output}")
    except Exception as e:
        raise Exception(f"Error assembling video: {str(e)}")


def assemble_video_simple(script_path: str, background_video: str, audio_file: str, output_path: str) -> str:
    """
    Simple video assembly without subtitles (fallback method)
    
    Args:
        script_path: Path to script.json file
        background_video: Path to background video file
        audio_file: Path to audio file
        output_path: Path for output video file
        
    Returns:
        Path to the assembled video file
    """
    try:
        # Check if all required files exist
        required_files = [script_path, background_video, audio_file]
        for file_path in required_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file not found: {file_path}")
        
        # Check for updated script with actual timings first
        script_path_updated = script_path.replace('.json', '_updated.json')
        if os.path.exists(script_path_updated):
            print("Found updated script with actual timings, using that...")
            script_path = script_path_updated
        
        # Load script data
        print("Loading script data...")
        script_data = load_script_json(script_path)
        scenes = script_data['scenes']
        
        # Get actual audio duration
        print("Getting actual audio duration...")
        actual_duration = get_audio_duration(audio_file)
        
        print(f"Script loaded: {script_data['title']}")
        print(f"Script duration: {script_data['duration_seconds']} seconds")
        print(f"Actual audio duration: {actual_duration:.2f} seconds")
        print(f"Scenes: {len(scenes)}")
        
        # Create input streams
        video_input = ffmpeg.input(background_video)
        audio_input = ffmpeg.input(audio_file)
        
        # Combine video and audio
        print("Combining video and audio...")
        output = ffmpeg.output(
            video_input,
            audio_input,
            output_path,
            vcodec='libx264',
            acodec='aac',
            preset='fast',
            crf=23,
            t=actual_duration,
            shortest=None
        )
        
        # Run the conversion
        print("Rendering final video...")
        ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        print(f"Video assembled: {output_path}")
        return output_path
        
    except ffmpeg.Error as e:
        stderr_output = e.stderr.decode('utf-8') if e.stderr else 'No stderr output'
        raise Exception(f"FFmpeg error: {stderr_output}")
    except Exception as e:
        raise Exception(f"Error assembling video: {str(e)}")


def main():
    """Main function for command line usage"""
    if len(sys.argv) < 5:
        print("Usage: python assemble.py <script_path> <background_video> <audio_file> <output_path>")
        print("Example: python assemble.py script.json background.mp4 speech.wav output.mp4")
        sys.exit(1)
    
    script_path = sys.argv[1]
    background_video = sys.argv[2]
    audio_file = sys.argv[3]
    output_path = sys.argv[4]
    
    try:
        # Try the new subtitle-based approach first
        print("Attempting to assemble video with subtitles...")
        result = assemble_video_with_subtitles(script_path, background_video, audio_file, output_path)
        print(f"Success: {result}")
        
    except Exception as e:
        print(f"Subtitle approach failed: {str(e)}")
        print("Falling back to simple video assembly...")
        
        try:
            result = assemble_video_simple(script_path, background_video, audio_file, output_path)
            print(f"Success: {result}")
        except Exception as e2:
            print(f"Error: {str(e2)}")
            sys.exit(1)


if __name__ == "__main__":
    main()