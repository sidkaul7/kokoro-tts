import os
import subprocess
from moviepy.editor import VideoFileClip

def split_video(input_path, segment_duration=120):  # 120 seconds = 2 minutes
    """Split a video into segments of specified duration using FFmpeg."""
    print(f"Loading video: {input_path}")
    video = VideoFileClip(input_path)
    
    # Get video duration
    total_duration = video.duration
    video.close()  # Close the video file as we'll use FFmpeg directly
    print(f"Total duration: {total_duration:.2f} seconds")
    
    # Calculate number of segments
    num_segments = int(total_duration // segment_duration) + (1 if total_duration % segment_duration > 0 else 0)
    print(f"Splitting into {num_segments} segments...")
    
    # Use the same directory as the input video
    output_dir = os.path.dirname(input_path)
    
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # Split video into segments using FFmpeg
    output_paths = []
    for i in range(num_segments):
        start_time = i * segment_duration
        duration = min(segment_duration, total_duration - start_time)
        
        # Generate output path
        output_path = os.path.join(output_dir, f"{base_name}_part{i+1}.mp4")
        
        # FFmpeg command to split video with audio
        print(f"Writing segment {i+1}/{num_segments}...")
        cmd = [
            'ffmpeg', '-y',  # Overwrite output files
            '-i', input_path,  # Input file
            '-ss', str(start_time),  # Start time
            '-t', str(duration),  # Duration
            '-c:v', 'copy',  # Copy video codec (no re-encoding)
            '-c:a', 'copy',  # Copy audio codec (no re-encoding)
            output_path
        ]
        
        # Run FFmpeg command
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            output_paths.append(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error processing segment {i+1}: {e}")
            continue
    
    print(f"Split complete! {len(output_paths)} segments created in {output_dir}")
    return output_paths

def main():
    # Get the most recent video from final_videos directory
    kokoro_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    final_videos_dir = os.path.join(kokoro_dir, "final_videos")
    if not os.path.exists(final_videos_dir):
        print("Error: final_videos directory not found")
        return
    
    # Get all video files and sort by modification time (newest first)
    # Exclude files that are already segments (contain '_part' in name)
    video_files = [f for f in os.listdir(final_videos_dir) if f.endswith('.mp4') and '_part' not in f]
    if not video_files:
        print("Error: No video files found in final_videos directory")
        return
    
    video_files.sort(key=lambda x: os.path.getmtime(os.path.join(final_videos_dir, x)), reverse=True)
    latest_video = os.path.join(final_videos_dir, video_files[0])
    
    # Split the video
    split_video(latest_video)

if __name__ == "__main__":
    main() 