import os
import sys
import time
import subprocess
from pathlib import Path
from moviepy.editor import VideoFileClip

def get_video_duration(video_path):
    """Get the duration of a video file in seconds."""
    try:
        with VideoFileClip(video_path) as video:
            return video.duration
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return None

def run_script(script_name, check_files=None):
    """Run a Python script and wait for it to complete."""
    print(f"\n{'='*50}")
    print(f"Running {script_name}...")
    print(f"{'='*50}\n")
    
    # Get the script path
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    # Run the script
    process = subprocess.Popen([sys.executable, script_path], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             universal_newlines=True)
    
    # Print output in real-time
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    
    # Get return code
    return_code = process.poll()
    
    if return_code != 0:
        print(f"Error: {script_name} failed with return code {return_code}")
        return False
    
    # If check_files is provided, verify the files exist
    if check_files:
        kokoro_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for file_pattern in check_files:
            # Get the most recent file matching the pattern
            if file_pattern.startswith("word_level_") or file_pattern.endswith(".wav"):
                search_dir = os.path.join(kokoro_dir, "last")  # Changed from kokoro_audio to last
            elif file_pattern.endswith(".mp4"):
                search_dir = os.path.join(kokoro_dir, "final_videos")
            else:
                search_dir = kokoro_dir
            
            files = list(Path(search_dir).glob(file_pattern))
            if not files:
                print(f"Error: No files found matching {file_pattern}")
                return False
            
            # Sort by modification time (newest first)
            latest_file = max(files, key=lambda x: x.stat().st_mtime)
            print(f"Found {latest_file}")
            
            # Return the latest file path if needed
            if file_pattern.endswith(".mp4"):
                return str(latest_file)
    
    return True

def main():
    # Step 1: Run format_json.py
    if not run_script("format_json.py"):
        print("Error: format_json.py failed")
        return
    
    # Step 2: Run auto_tts.py and check for output files
    if not run_script("auto_tts.py", check_files=[
        "word_level_*.srt",  # Check for word-level subtitles
        "*.wav"  # Check for audio file
    ]):
        print("Error: auto_tts.py failed")
        return
    
    # Step 3: Run create_final_video.py and check for output file
    final_video_path = run_script("create_final_video.py", check_files=[
        "final_video_*.mp4"  # Check for final video
    ])
    if not final_video_path:
        print("Error: create_final_video.py failed")
        return
    
    # Check video duration before running split_video.py
    duration = get_video_duration(final_video_path)
    if duration is None:
        print("Error: Could not determine video duration")
        return
        
    if duration <= 120:
        print(f"\nVideo duration is {duration:.2f} seconds (≤ 120 seconds)")
        print("Skipping split_video.py as video is short enough")
    else:
        print(f"\nVideo duration is {duration:.2f} seconds (> 120 seconds)")
        print("Running split_video.py...")
        # Step 4: Run split_video.py and check for output files
        if not run_script("split_video.py", check_files=[
            "final_video_*_part*.mp4"  # Check for split video parts
        ]):
            print("Error: split_video.py failed")
            return
    
    print("\nAll steps completed successfully!")

if __name__ == "__main__":
    main() 