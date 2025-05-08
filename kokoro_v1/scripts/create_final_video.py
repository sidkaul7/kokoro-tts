import os
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import pysrt
from datetime import datetime
import random

def time_to_seconds(time_obj):
    """Convert SRT time object to seconds."""
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000

def create_subtitle_clips(video_width, video_height, subtitles):
    """Create TextClips for each subtitle."""
    text_clips = []
    
    for subtitle in subtitles:
        start_time = time_to_seconds(subtitle.start)
        end_time = time_to_seconds(subtitle.end)
        duration = end_time - start_time
        
        # Create text clip
        text_clip = (TextClip(subtitle.text, 
                             fontsize=70,
                             color='yellow',
                             font='Arial-Bold',
                             stroke_color='black',
                             stroke_width=2,
                             size=(video_width * 0.8, None),  # Limit width to 80% of video width
                             method='caption')
                    .set_position(('center', 'center'))
                    .set_duration(duration)
                    .set_start(start_time))
        
        text_clips.append(text_clip)
    
    return text_clips

def create_final_video(background_video_path, audio_path, srt_path, output_path):
    """Create final video with background, audio, and subtitles."""
    print("Loading background video...")
    background = VideoFileClip(background_video_path)
    
    print("Loading audio file...")
    audio = AudioFileClip(audio_path)
    
    print("Loading subtitles...")
    subtitles = pysrt.open(srt_path)
    
    # Calculate required video duration
    video_duration = audio.duration
    
    # Loop background video if needed
    if background.duration < video_duration:
        background = background.loop(duration=video_duration)
    else:
        background = background.subclip(0, video_duration)
    
    # Set audio
    background = background.set_audio(audio)
    
    # Create subtitle clips
    print("Creating subtitle clips...")
    subtitle_clips = create_subtitle_clips(background.w, background.h, subtitles)
    
    # Combine everything
    print("Compositing final video...")
    final_video = CompositeVideoClip([background] + subtitle_clips)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write final video
    print("Writing final video...")
    final_video.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile="temp-audio.m4a",
        remove_temp=True
    )
    
    # Clean up
    background.close()
    audio.close()
    final_video.close()
    
    print(f"Video created successfully: {output_path}")

def main():
    # Define paths - now accounting for scripts directory
    kokoro_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one more level
    last_dir = os.path.join(kokoro_dir, "last")
    
    # Find the word-level SRT and audio files in the last directory
    srt_files = [f for f in os.listdir(last_dir) if f.startswith("word_level_") and f.endswith(".srt")]
    wav_files = [f for f in os.listdir(last_dir) if f.endswith(".wav")]
    
    if not srt_files or not wav_files:
        print("Error: Could not find required SRT and WAV files in the 'last' directory")
        return
    
    # Use the files from the last directory
    srt_path = os.path.join(last_dir, srt_files[0])
    audio_path = os.path.join(last_dir, wav_files[0])
    
    # Define output path
    output_dir = os.path.join(kokoro_dir, "final_videos")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"final_video_{timestamp}.mp4")
    
    # Get background video path and randomly select one
    background_video_dir = os.path.join(kokoro_dir, "background_videos")
    background_videos = [f for f in os.listdir(background_video_dir) if f.endswith('.mp4')]
    
    if not background_videos:
        print(f"Error: No background videos found in {background_video_dir}")
        return
    
    # Randomly select a background video
    selected_video = random.choice(background_videos)
    background_video_path = os.path.join(background_video_dir, selected_video)
    print(f"Selected background video: {selected_video}")
    
    # Create final video
    create_final_video(background_video_path, audio_path, srt_path, output_path)

if __name__ == "__main__":
    main() 