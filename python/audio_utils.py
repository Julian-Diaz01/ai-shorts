#!/usr/bin/env python3
"""
Audio utility functions for duration detection and processing
"""

import os
import subprocess
import json
from pathlib import Path

def get_audio_duration(audio_file_path: str) -> float:
    """
    Get the duration of an audio file using FFprobe
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Duration in seconds as a float
    """
    try:
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Use ffprobe to get audio duration
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            audio_file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        duration = float(data['format']['duration'])
        return duration
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFprobe error: {e.stderr}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing FFprobe output: {e}")
    except Exception as e:
        raise Exception(f"Error getting audio duration: {e}")

def get_audio_info(audio_file_path: str) -> dict:
    """
    Get detailed information about an audio file
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Dictionary with audio information
    """
    try:
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Use ffprobe to get detailed audio info
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            audio_file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Extract audio stream info
        audio_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'audio':
                audio_stream = stream
                break
        
        if not audio_stream:
            raise Exception("No audio stream found in file")
        
        info = {
            'duration': float(data['format']['duration']),
            'sample_rate': int(audio_stream.get('sample_rate', 0)),
            'channels': int(audio_stream.get('channels', 0)),
            'codec': audio_stream.get('codec_name', 'unknown'),
            'bitrate': int(data['format'].get('bit_rate', 0)) if data['format'].get('bit_rate') else 0
        }
        
        return info
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFprobe error: {e.stderr}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing FFprobe output: {e}")
    except Exception as e:
        raise Exception(f"Error getting audio info: {e}")

def main():
    """Test function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python audio_utils.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    try:
        duration = get_audio_duration(audio_file)
        info = get_audio_info(audio_file)
        
        print(f"Audio file: {audio_file}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Sample rate: {info['sample_rate']} Hz")
        print(f"Channels: {info['channels']}")
        print(f"Codec: {info['codec']}")
        print(f"Bitrate: {info['bitrate']} bps")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
