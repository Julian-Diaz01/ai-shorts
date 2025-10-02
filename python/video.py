import os
import sys
import json
import ffmpeg
from typing import Dict, Any, Tuple


def load_config() -> Dict[str, Any]:
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")
        return {}


def get_video_info(input_path: str) -> Dict[str, Any]:
    try:
        probe = ffmpeg.probe(input_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        
        if not video_stream:
            raise Exception("No video stream found")
        
        return {
            'width': int(video_stream['width']),
            'height': int(video_stream['height']),
            'duration': float(video_stream['duration']),
            'fps': eval(video_stream['r_frame_rate']),
            'codec': video_stream['codec_name']
        }
    except Exception as e:
        raise Exception(f"Error getting video info: {str(e)}")


def crop_video_to_9_16(input_path: str, output_path: str) -> None:
    try:
        # Get video info
        info = get_video_info(input_path)
        width = info['width']
        height = info['height']
        
        # Calculate crop parameters for 9:16 aspect ratio
        target_width = 720
        target_height = 1280
        
        # Calculate crop dimensions
        if width / height > target_width / target_height:
            # Video is wider than target, crop width
            crop_width = int(height * target_width / target_height)
            crop_height = height
            x_offset = (width - crop_width) // 2
            y_offset = 0
        else:
            # Video is taller than target, crop height
            crop_width = width
            crop_height = int(width * target_height / target_width)
            x_offset = 0
            y_offset = (height - crop_height) // 2
        
        print(f"Original: {width}x{height}")
        print(f"Cropping to: {crop_width}x{crop_height} at offset ({x_offset}, {y_offset})")
        
        # Create input stream
        input_stream = ffmpeg.input(input_path)
        
        # Crop video
        cropped = ffmpeg.crop(input_stream, x_offset, y_offset, crop_width, crop_height)
        
        # Scale to target resolution
        scaled = ffmpeg.filter(cropped, 'scale', target_width, target_height)
        
        # Output
        output = ffmpeg.output(scaled, output_path, vcodec='libx264', preset='fast', crf=23)
        
        # Run conversion
        ffmpeg.run(output, overwrite_output=True, quiet=True)
        
        print(f"Video cropped to 9:16: {output_path}")
        
    except Exception as e:
        raise Exception(f"Error cropping video: {str(e)}")


def trim_video_to_duration(input_path: str, output_path: str, target_duration: float) -> None:
    try:
        # Get video info
        info = get_video_info(input_path)
        current_duration = info['duration']
        
        print(f"Current duration: {current_duration:.2f} seconds")
        print(f"Target duration: {target_duration:.2f} seconds")
        
        if current_duration <= target_duration:
            print("Video is already short enough, copying...")
            import shutil
            shutil.copy2(input_path, output_path)
            return
        
        # Create input stream
        input_stream = ffmpeg.input(input_path)
        
        # Trim video
        trimmed = ffmpeg.filter(input_stream, 'trim', duration=target_duration)
        
        # Output
        output = ffmpeg.output(trimmed, output_path, vcodec='libx264', preset='fast', crf=23)
        
        # Run conversion
        ffmpeg.run(output, overwrite_output=True, quiet=True)
        
        print(f"Video trimmed to {target_duration:.2f} seconds: {output_path}")
        
    except Exception as e:
        raise Exception(f"Error trimming video: {str(e)}")


def loop_video_to_duration(input_path: str, output_path: str, target_duration: float) -> None:
    try:
        # Get video info
        info = get_video_info(input_path)
        current_duration = info['duration']
        
        print(f"Current duration: {current_duration:.2f} seconds")
        print(f"Target duration: {target_duration:.2f} seconds")
        
        if current_duration >= target_duration:
            print("Video is already long enough, trimming...")
            trim_video_to_duration(input_path, output_path, target_duration)
            return
        
        # Calculate number of loops needed
        loops_needed = int(target_duration / current_duration) + 1
        
        print(f"Looping video {loops_needed} times...")
        
        # Create input stream
        input_stream = ffmpeg.input(input_path)
        
        # Loop video
        looped = ffmpeg.filter(input_stream, 'loop', loop=loops_needed, size=32767, start=0)
        
        # Trim to exact duration
        trimmed = ffmpeg.filter(looped, 'trim', duration=target_duration)
        
        # Output
        output = ffmpeg.output(trimmed, output_path, vcodec='libx264', preset='fast', crf=23)
        
        # Run conversion
        ffmpeg.run(output, overwrite_output=True, quiet=True)
        
        print(f"Video looped to {target_duration:.2f} seconds: {output_path}")
        
    except Exception as e:
        raise Exception(f"Error looping video: {str(e)}")


def prepare_background_video(input_path: str, output_path: str, target_duration: float) -> None:
    try:
        # First crop to 9:16 aspect ratio
        temp_cropped = output_path.replace('.mp4', '_cropped.mp4')
        crop_video_to_9_16(input_path, temp_cropped)
        
        # Then adjust duration
        if target_duration > 0:
            loop_video_to_duration(temp_cropped, output_path, target_duration)
        else:
            # Just copy the cropped video
            import shutil
            shutil.copy2(temp_cropped, output_path)
        
        # Clean up temp file
        if os.path.exists(temp_cropped):
            os.remove(temp_cropped)
        
        print(f"Background video prepared: {output_path}")
        
    except Exception as e:
        raise Exception(f"Error preparing background video: {str(e)}")


def add_subtitles_to_video(video_path: str, subtitle_path: str, output_path: str) -> None:
    try:
        # Get subtitle file extension
        subtitle_ext = os.path.splitext(subtitle_path)[1].lower()
        
        if subtitle_ext == '.srt':
            subtitle_filter = 'subtitles'
        elif subtitle_ext == '.ass':
            subtitle_filter = 'ass'
        elif subtitle_ext == '.vtt':
            subtitle_filter = 'subtitles'
        else:
            raise ValueError(f"Unsupported subtitle format: {subtitle_ext}")
        
        print(f"Adding subtitles using {subtitle_filter} filter...")
        
        # Create input stream (this will include both video and audio if present)
        input_stream = ffmpeg.input(video_path)
        
        # Add subtitles to video stream only
        if subtitle_filter == 'ass':
            subtitled = ffmpeg.filter(input_stream['v'], 'ass', subtitle_path)
        else:
            subtitled = ffmpeg.filter(input_stream['v'], 'subtitles', subtitle_path)
        
        # Output with both video and audio streams
        output = ffmpeg.output(
            subtitled, 
            input_stream['a'],  # Include audio stream
            output_path, 
            vcodec='libx264', 
            acodec='aac',
            preset='fast', 
            crf=23
        )
        
        # Run conversion
        ffmpeg.run(output, overwrite_output=True, quiet=True)
        
        print(f"Video with subtitles created: {output_path}")
        
    except Exception as e:
        raise Exception(f"Error adding subtitles to video: {str(e)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python video.py <command> [args...]")
        print("Commands:")
        print("  info <video_file> - Get video information")
        print("  crop <input> <output> - Crop to 9:16 aspect ratio")
        print("  trim <input> <output> <duration> - Trim to duration")
        print("  loop <input> <output> <duration> - Loop to duration")
        print("  prepare <input> <output> <duration> - Prepare background video")
        print("  subtitles <video> <subtitle> <output> - Add subtitles")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "info":
            if len(sys.argv) < 3:
                print("Usage: python video.py info <video_file>")
                sys.exit(1)
            
            video_file = sys.argv[2]
            info = get_video_info(video_file)
            print(f"Video info: {info}")
        
        elif command == "crop":
            if len(sys.argv) < 4:
                print("Usage: python video.py crop <input> <output>")
                sys.exit(1)
            
            input_path = sys.argv[2]
            output_path = sys.argv[3]
            crop_video_to_9_16(input_path, output_path)
        
        elif command == "trim":
            if len(sys.argv) < 5:
                print("Usage: python video.py trim <input> <output> <duration>")
                sys.exit(1)
            
            input_path = sys.argv[2]
            output_path = sys.argv[3]
            duration = float(sys.argv[4])
            trim_video_to_duration(input_path, output_path, duration)
        
        elif command == "loop":
            if len(sys.argv) < 5:
                print("Usage: python video.py loop <input> <output> <duration>")
                sys.exit(1)
            
            input_path = sys.argv[2]
            output_path = sys.argv[3]
            duration = float(sys.argv[4])
            loop_video_to_duration(input_path, output_path, duration)
        
        elif command == "prepare":
            if len(sys.argv) < 5:
                print("Usage: python video.py prepare <input> <output> <duration>")
                sys.exit(1)
            
            input_path = sys.argv[2]
            output_path = sys.argv[3]
            duration = float(sys.argv[4])
            prepare_background_video(input_path, output_path, duration)
        
        elif command == "subtitles":
            if len(sys.argv) < 5:
                print("Usage: python video.py subtitles <video> <subtitle> <output>")
                sys.exit(1)
            
            video_path = sys.argv[2]
            subtitle_path = sys.argv[3]
            output_path = sys.argv[4]
            add_subtitles_to_video(video_path, subtitle_path, output_path)
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
