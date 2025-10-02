#!/usr/bin/env python3
"""
Video Preparation Script
Processes stock video files to create 30-second background videos
"""

import sys
import os
import ffmpeg
from pathlib import Path
import math
import random

def get_video_duration(input_path: str) -> float:
    """
    Get the duration of a video file in seconds
    
    Args:
        input_path: Path to the input video file
        
    Returns:
        Duration in seconds
    """
    try:
        probe = ffmpeg.probe(input_path)
        duration = float(probe['streams'][0]['duration'])
        return duration
    except Exception as e:
        raise Exception(f"Error getting video duration: {str(e)}")

def trim_video_to_duration(input_path: str, output_path: str, target_duration: float = 30.0) -> str:
    """
    Trim video to exact duration by cutting from a random start point
    
    Args:
        input_path: Path to input video file
        output_path: Path for output video file
        target_duration: Target duration in seconds (can be float for precise timing)
        
    Returns:
        Success message with file path
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Check if input file exists
        if not os.path.exists(input_path):
            return f"Error: Input file does not exist: {input_path}"
        
        # Get video duration
        duration = get_video_duration(input_path)
        print(f"Input video duration: {duration:.2f} seconds")
        
        if duration <= target_duration:
            return f"Error: Video is already {duration:.2f} seconds or shorter. Use loop_video instead."
        
        # Choose random start point (but leave enough room for target_duration)
        max_start_time = max(0, duration - target_duration - 5)  # Leave 5 seconds buffer
        random_start = random.uniform(0, max_start_time)
        print(f"Random start point: {random_start:.2f} seconds")
        print(f"Target duration: {target_duration:.2f} seconds")
        
        # Trim video to target duration with mobile aspect ratio (9:16) by cropping
        (
            ffmpeg
            .input(input_path, ss=random_start, t=target_duration)
            .output(output_path, 
                   vcodec='libx264',
                   acodec='aac',
                   preset='fast',
                   crf=23,
                   vf='scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280')  # Crop to 9:16 aspect ratio
            .overwrite_output()
            .run(quiet=True)
        )
        
        return f"Video trimmed successfully: {output_path}"
        
    except ffmpeg.Error as e:
        return f"FFmpeg error: {str(e)}"
    except Exception as e:
        return f"Error trimming video: {str(e)}"

def loop_video_to_duration(input_path: str, output_path: str, target_duration: float = 30.0) -> str:
    """
    Loop video to reach target duration
    
    Args:
        input_path: Path to input video file
        output_path: Path for output video file
        target_duration: Target duration in seconds
        
    Returns:
        Success message with file path
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Check if input file exists
        if not os.path.exists(input_path):
            return f"Error: Input file does not exist: {input_path}"
        
        # Get video duration
        duration = get_video_duration(input_path)
        print(f"Input video duration: {duration:.2f} seconds")
        
        if duration >= target_duration:
            return f"Error: Video is already {duration:.2f} seconds or longer. Use trim_video instead."
        
        # Calculate how many loops we need
        loops_needed = math.ceil(target_duration / duration)
        print(f"Need to loop video {loops_needed} times to reach {target_duration} seconds")
        
        # Create input stream
        input_stream = ffmpeg.input(input_path)
        
        # Loop the video
        looped_video = input_stream
        for _ in range(loops_needed - 1):
            looped_video = ffmpeg.concat(looped_video, input_stream, v=1, a=1)
        
        # Trim to exact target duration with mobile aspect ratio (9:16) by cropping
        (
            looped_video
            .output(output_path,
                   vcodec='libx264',
                   acodec='aac',
                   preset='fast',
                   crf=23,
                   vf='scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280',
                   t=target_duration)  # Trim to exact duration
            .overwrite_output()
            .run(quiet=True)
        )
        
        return f"Video looped successfully: {output_path}"
        
    except ffmpeg.Error as e:
        return f"FFmpeg error: {str(e)}"
    except Exception as e:
        return f"Error looping video: {str(e)}"

def prepare_background_video(input_path: str, output_path: str, target_duration: float = 30.0) -> str:
    """
    Prepare background video by trimming or looping to exact duration
    
    Args:
        input_path: Path to input video file
        output_path: Path for output video file
        target_duration: Target duration in seconds
        
    Returns:
        Success message with file path
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            return f"Error: Input file does not exist: {input_path}"
        
        # Get video duration
        duration = get_video_duration(input_path)
        print(f"Processing video: {input_path}")
        print(f"Original duration: {duration:.2f} seconds")
        print(f"Target duration: {target_duration} seconds")
        
        # Decide whether to trim or loop
        if duration > target_duration:
            print("Video is longer than target duration. Trimming...")
            return trim_video_to_duration(input_path, output_path, target_duration)
        elif duration < target_duration:
            print("Video is shorter than target duration. Looping...")
            return loop_video_to_duration(input_path, output_path, target_duration)
        else:
            print("Video is already the correct duration. Converting to mobile format...")
            # Convert to mobile aspect ratio by cropping
            (
                ffmpeg
                .input(input_path)
                .output(output_path,
                       vcodec='libx264',
                       acodec='aac',
                       preset='fast',
                       crf=23,
                       vf='scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280')
                .overwrite_output()
                .run(quiet=True)
            )
            return f"Video converted to mobile format successfully: {output_path}"
            
    except Exception as e:
        return f"Error preparing background video: {str(e)}"

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python prepare_video.py <input_video> [output_path] [target_duration]")
        print("Example: python prepare_video.py minecraft_runner.mp4 ../output/background.mp4 30")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "../output/background.mp4"
    target_duration = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
    
    # Convert relative paths to absolute paths
    if not os.path.isabs(input_path):
        input_path = os.path.abspath(input_path)
    
    if not os.path.isabs(output_path):
        output_path = os.path.abspath(output_path)
    
    result = prepare_background_video(input_path, output_path, target_duration)
    print(result)

if __name__ == "__main__":
    main()
