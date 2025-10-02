import os
import json
import tempfile
from typing import Dict, List, Any, Tuple


def load_config() -> Dict[str, Any]:
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")
        return {}




def create_ass_subtitle(scenes: List[Dict[str, Any]], output_path: str) -> None:
    config = load_config()
    text_config = config.get('text_overlay', {})
    video_config = config.get('video', {})
    
    # Get styling from config with defaults
    font_name = text_config.get('font', 'Arial')
    font_size = text_config.get('font_size', 48)
    font_color = text_config.get('font_color', 'white')
    bg_color = text_config.get('background_color', 'black@0.7')
    border_width = text_config.get('border_width', 5)
    position = text_config.get('position', 'center')
    
    # Get video resolution from config
    resolution = video_config.get('resolution', '720x1280')
    
    # Handle both string and dict formats
    if isinstance(resolution, dict):
        width = resolution.get('width', 720)
        height = resolution.get('height', 1280)
    else:
        # String format like "720x1280"
        width, height = map(int, resolution.split('x'))
    
    # Calculate margins based on resolution
    margin = int(width * 0.08)  # 8% margin on each side
    
    # Calculate alignment based on position
    alignment_map = {
        'top': 8,      # center-top
        'upper_third': 5,  # center-bottom (upper third)
        'center': 2,   # center
        'lower_third': 5,  # center-bottom (lower third)
        'bottom': 2    # center
    }
    alignment = alignment_map.get(position, 2)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write ASS header with dynamic resolution
            f.write("[Script Info]\n")
            f.write("Title: YouTube Short Subtitles\n")
            f.write("ScriptType: v4.00+\n")
            f.write("WrapStyle: 2\n")
            f.write("ScaledBorderAndShadow: yes\n")
            f.write(f"PlayResX: {width}\n")
            f.write(f"PlayResY: {height}\n\n")
            
            # Write styles
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            
            # Convert colors
            primary_color = convert_color_to_ass(font_color)
            outline_color = convert_color_to_ass('black')
            back_color = convert_color_to_ass(bg_color)
            
            # Create dynamic style with background box enabled
            # BorderStyle: 1 = outline + shadow, 3 = box
            # Outline: border width, Shadow: shadow depth
            f.write(f"Style: Default,{font_name},{font_size},{primary_color},{primary_color},{outline_color},{back_color},0,0,0,0,100,100,0,0,3,{border_width},0,{alignment},{margin},{margin},{margin},1\n\n")
            
            # Write events
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            for i, scene in enumerate(scenes):
                start_time = format_timestamp_ass(scene['start'])
                end_time = format_timestamp_ass(scene['end'])
                text = scene['voice']
                
                # Process text for multi-line and overflow prevention
                processed_text = process_text_for_ass(text, font_size, width, margin)
                
                # Properly escape text for ASS format (fix backslash visibility)
                escaped_text = escape_text_for_ass(processed_text)
                
                f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{escaped_text}\n")
        
        print(f"ASS subtitle file created: {output_path}")
        
    except Exception as e:
        raise Exception(f"Error creating ASS subtitle: {str(e)}")


def process_text_for_ass(text: str, font_size: int, width: int, margin: int) -> str:
    # Ensure text is a string
    if not isinstance(text, str):
        print(f"Warning: Expected string but got {type(text)}: {text}")
        text = str(text)
    
    # Handle empty or None text
    if not text or text.strip() == "":
        return ""
    
    # Calculate max characters per line based on available width
    # Available width: width - (2 * margin)
    available_width = width - (2 * margin)
    # Approximate character width: font_size * 0.6
    char_width = font_size * 0.6
    max_chars_per_line = int(available_width / char_width)
    
    # Ensure minimum of 15 characters per line
    max_chars_per_line = max(15, max_chars_per_line)
    
    # Split text into words
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        # Check if adding this word would exceed the limit
        if len(current_line + " " + word) <= max_chars_per_line:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            # Start a new line
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Word is too long, add it anyway
                lines.append(word)
    
    # Add the last line
    if current_line:
        lines.append(current_line)
    
    # Join lines with \\N for ASS format
    return "\\N".join(lines)


def escape_text_for_ass(text: str) -> str:
    # Handle ASS line breaks properly - convert \\N to actual line breaks
    # ASS format uses \N for line breaks, not \\N
    escaped = text.replace('\\N', '\\N')
    
    # Escape other special characters that need escaping in ASS
    escaped = escaped.replace('{', '\\{')
    escaped = escaped.replace('}', '\\}')
    
    # Escape backslashes that are not part of ASS commands
    # But preserve ASS commands like \N, \b, \i, etc.
    import re
    # Replace backslashes that are not followed by a letter (ASS command)
    escaped = re.sub(r'\\(?![a-zA-Z])', '\\\\', escaped)
    
    return escaped


def convert_color_to_ass(color: str) -> str:
    color_map = {
        'white': '&H00FFFFFF',
        'black': '&H00000000',
        'red': '&H000000FF',
        'green': '&H0000FF00',
        'blue': '&H00FF0000',
        'yellow': '&H0000FFFF',
        'cyan': '&H00FFFF00',
        'magenta': '&H00FF00FF'
    }
    
    # Handle transparency
    if '@' in color:
        base_color = color.split('@')[0]
        alpha_str = color.split('@')[1]
        
        # Convert alpha to hex (0.0-1.0 to 0-255)
        try:
            alpha_float = float(alpha_str)
            alpha_hex = hex(int(alpha_float * 255))[2:].upper().zfill(2)
        except:
            alpha_hex = 'FF'  # Default to opaque
        
        # Get base color and replace alpha
        base_ass_color = color_map.get(base_color, '&H00FFFFFF')
        return base_ass_color[:-2] + alpha_hex
    
    return color_map.get(color, '&H00FFFFFF')


def format_timestamp_ass(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"




def create_subtitle_file(scenes: List[Dict[str, Any]], output_path: str) -> str:
    subtitle_path = f"{output_path}.ass"
    create_ass_subtitle(scenes, subtitle_path)
    return subtitle_path


def create_subtitle_file_from_json(scenes_json_path: str, output_path: str) -> str:
    try:
        # Load scenes data
        with open(scenes_json_path, 'r') as f:
            scenes_data = json.load(f)
        
        # Extract scenes from the scenes.json structure
        if 'scenes' in scenes_data and len(scenes_data['scenes']) > 0:
            # Get the first scene's example_script
            first_scene = scenes_data['scenes'][0]
            if 'example_script' in first_scene:
                script_data = first_scene['example_script']
                scenes = script_data.get('scenes', [])
            else:
                scenes = []
        else:
            scenes = []
        
        if not scenes:
            raise Exception("No scenes found in scenes.json")
        
        # Create subtitle file
        subtitle_path = f"{output_path}.ass"
        create_ass_subtitle(scenes, subtitle_path)
        return subtitle_path
        
    except Exception as e:
        raise Exception(f"Error creating subtitle from scenes.json: {str(e)}")


def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python text.py <scenes_json> <output_path>")
        sys.exit(1)
    
    scenes_json = sys.argv[1]
    output_path = sys.argv[2]
    
    try:
        # Load scenes data
        with open(scenes_json, 'r') as f:
            scenes_data = json.load(f)
        
        # Extract scenes from the scenes.json structure
        if 'scenes' in scenes_data and len(scenes_data['scenes']) > 0:
            # Get the first scene's example_script
            first_scene = scenes_data['scenes'][0]
            if 'example_script' in first_scene:
                script_data = first_scene['example_script']
                scenes = script_data.get('scenes', [])
            else:
                scenes = []
        else:
            scenes = []
        
        if not scenes:
            print("No scenes found in the data")
            sys.exit(1)
        
        # Create subtitle file (ASS format only)
        subtitle_path = create_subtitle_file(scenes, output_path)
        print(f"ASS subtitle file created: {subtitle_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
