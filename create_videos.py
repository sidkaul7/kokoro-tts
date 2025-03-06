from gtts import gTTS
intro_text = "Reddit Asks"
tts = gTTS(intro_text)
tts.save("reddit_asks_audio.mp3")

# Install required packages
!apt-get update -qq
!apt-get install -y ffmpeg imagemagick
!pip install -q moviepy SpeechRecognition gTTS pysubs2

# Fix ImageMagick policy to allow necessary operations
!sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml
!sed -i 's/<policy domain="path" rights="none" pattern="@\*"/<!-- \0 -->/' /etc/ImageMagick-6/policy.xml

# Verify the policy was updated properly
!grep -A 1 "domain=\"path\"" /etc/ImageMagick-6/policy.xml

import os
import json
import random
from pathlib import Path
import speech_recognition as sr
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips
from google.colab import files
import datetime
import time
from gtts import gTTS
import pysubs2
from pysubs2 import SSAFile, SSAEvent, SSAStyle, make_time
import subprocess

def find_minecraft_videos(video_dir="minecraft_videos"):
    """Find Minecraft videos in the specified directory."""
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov']
    video_files = []
    try:
        for file in os.listdir(video_dir):
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(video_dir, file))
        if not video_files:
            print(f"No Minecraft videos found in {video_dir}. Please upload a Minecraft video first.")
        return video_files
    except FileNotFoundError:
        print(f"Directory {video_dir} not found. Creating it now.")
        os.makedirs(video_dir)
        print("Please upload your Minecraft gameplay video.")
        return []

def upload_minecraft_video():
    """Allow user to upload a Minecraft video in Colab."""
    print("Please upload a Minecraft gameplay video file (.mp4, .mkv, .avi, or .mov):")
    os.makedirs("minecraft_videos", exist_ok=True)
    uploaded = files.upload()
    for filename in uploaded.keys():
        if filename.endswith(('.mp4', '.mkv', '.avi', '.mov')):
            dest_path = os.path.join("/content/drive/MyDrive/YouTUBE REDDIT/minecraft_videos", filename)
            with open(dest_path, 'wb') as f:
                f.write(uploaded[filename])
            print(f"Successfully saved {filename} to {dest_path}")
            return dest_path
    print("No valid video file was uploaded.")
    return None

def split_text_into_chunks(text, max_words=4):
    """Split text into chunks of max_words for subtitles."""
    words = text.split()
    return [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

def calculate_content_duration(posts):
    """Calculate the total duration of posts and comments, including author narration."""
    total_duration = 0
    intro_audio_file = "reddit_asks_audio.mp3"
    if not os.path.exists(intro_audio_file):
        tts = gTTS("Reddit Asks")
        tts.save(intro_audio_file)
    intro_audio = AudioFileClip(intro_audio_file)
    total_duration += intro_audio.duration + 1

    for post in posts:
        title_text = post.get('title', 'Post')
        title_audio_file = post.get('title_audio_file', f"title_audio_{total_duration}.mp3")
        if not os.path.exists(title_audio_file):
            tts = gTTS(title_text)
            tts.save(title_audio_file)
        title_audio = AudioFileClip(title_audio_file)
        total_duration += title_audio.duration + 1

        for comment in post.get('top_comments', []):
            author_text = "User says"
            author_audio_file = f"author_audio_{total_duration}.mp3"
            if not os.path.exists(author_audio_file):
                tts = gTTS(author_text)
                tts.save(author_audio_file)
            author_audio = AudioFileClip(author_audio_file)
            total_duration += author_audio.duration

            audio_file = comment.get('audio_file')
            if audio_file and os.path.exists(audio_file):
                audio_clip = AudioFileClip(audio_file)
                total_duration += audio_clip.duration + 1

    return total_duration

def select_content_for_duration(reddit_data, target_duration):
    """Select posts and comments to fit within the target duration, including author narration."""
    selected_posts = []
    current_duration = 0
    intro_audio_file = "reddit_asks_audio.mp3"
    if not os.path.exists(intro_audio_file):
        tts = gTTS("Reddit Asks")
        tts.save(intro_audio_file)
    intro_audio = AudioFileClip(intro_audio_file)
    current_duration += intro_audio.duration + 1

    for post in reddit_data:
        if current_duration >= target_duration:
            break

        title_text = post.get('title', 'Post')
        title_audio_file = post.get('title_audio_file', f"title_audio_{current_duration}.mp3")
        if not os.path.exists(title_audio_file):
            tts = gTTS(title_text)
            tts.save(title_audio_file)
        title_audio = AudioFileClip(title_audio_file)
        title_duration = title_audio.duration + 1

        if current_duration + title_duration > target_duration:
            continue

        selected_post = post.copy()
        selected_post['top_comments'] = []
        current_duration += title_duration

        for comment in post.get('top_comments', []):
            if current_duration >= target_duration:
                break
            author_text = "User says"
            author_audio_file = f"author_audio_{current_duration}.mp3"
            if not os.path.exists(author_audio_file):
                tts = gTTS(author_text)
                tts.save(author_audio_file)
            author_audio = AudioFileClip(author_audio_file)
            author_duration = author_audio.duration

            audio_file = comment.get('audio_file')
            if audio_file and os.path.exists(audio_file):
                audio_clip = AudioFileClip(audio_file)
                comment_duration = author_duration + audio_clip.duration + 1
                if current_duration + comment_duration <= target_duration:
                    selected_post['top_comments'].append(comment)
                    current_duration += comment_duration

        if selected_post['top_comments']:
            selected_posts.append(selected_post)

    return selected_posts, current_duration

def create_ass_subtitles(reddit_data, video_width, video_height, output_file="subtitles.ass"):
    """Create an ASS subtitle file with static subtitles near the bottom."""
    subs = SSAFile()

    subs.styles["Default"] = SSAStyle(
        fontname="DejaVu Sans",
        fontsize=25,
        primarycolor=pysubs2.Color(255, 255, 0),
        outlinecolor=pysubs2.Color(0, 0, 0),
        backcolor=pysubs2.Color(0, 0, 0, 255),
        bold=True,
        outline=4,
        shadow=0,
        alignment=2,
        marginl=10,
        marginr=10,
        marginv=30
    )

    current_position = 0

    intro_audio_file = "reddit_asks_audio.mp3"
    if not os.path.exists(intro_audio_file):
        tts = gTTS("Reddit Asks")
        tts.save(intro_audio_file)
    intro_audio = AudioFileClip(intro_audio_file)
    intro_duration = intro_audio.duration
    subs.append(SSAEvent(
        start=make_time(s=current_position),
        end=make_time(s=current_position + intro_duration),
        text="Reddit Asks"
    ))
    current_position += intro_duration + 1

    for post in reddit_data:
        title_text = post.get('title', 'Post')
        title_audio_file = post.get('title_audio_file', f"title_audio_{current_position}.mp3")
        if not os.path.exists(title_audio_file):
            tts = gTTS(title_text)
            tts.save(title_audio_file)
        title_audio = AudioFileClip(title_audio_file)
        title_duration = title_audio.duration

        title_chunks = split_text_into_chunks(title_text)
        chunk_duration = title_duration / len(title_chunks) if title_chunks else title_duration
        for i, chunk in enumerate(title_chunks):
            start_time = current_position + (i * chunk_duration)
            subs.append(SSAEvent(
                start=make_time(s=start_time),
                end=make_time(s=start_time + chunk_duration),
                text=chunk
            ))
        current_position += title_duration + 1

        for comment in post.get('top_comments', []):
            author_text = "User says"
            author_audio_file = f"author_audio_{current_position}.mp3"
            if not os.path.exists(author_audio_file):
                tts = gTTS(author_text)
                tts.save(author_audio_file)
            author_audio = AudioFileClip(author_audio_file)
            author_duration = author_audio.duration

            subs.append(SSAEvent(
                start=make_time(s=current_position),
                end=make_time(s=current_position + author_duration),
                text=author_text
            ))
            current_position += author_duration

            audio_file = comment.get('audio_file')
            if audio_file and os.path.exists(audio_file):
                audio_clip = AudioFileClip(audio_file)
                audio_duration = audio_clip.duration
                subtitle_text = comment.get('body', '')
                subtitle_chunks = split_text_into_chunks(subtitle_text)
                chunk_duration = audio_duration / len(subtitle_chunks) if subtitle_chunks else audio_duration

                for i, chunk in enumerate(subtitle_chunks):
                    start_time = current_position + (i * chunk_duration)
                    subs.append(SSAEvent(
                        start=make_time(s=start_time),
                        end=make_time(s=start_time + chunk_duration),
                        text=chunk
                    ))
                current_position += audio_duration + 1

    subs.save(output_file)
    return output_file, current_position

def create_video_with_subtitles(json_file, background_video_path, target_duration, output_file="reddit_video.mp4"):
    """Create a video with ASS subtitles using FFmpeg, replaying background if needed."""
    with open(json_file, 'r', encoding='utf-8') as f:
        reddit_data = json.load(f)

    final_content, final_duration = select_content_for_duration(reddit_data, target_duration)

    background_video = VideoFileClip(background_video_path).without_audio()
    video_width, video_height = background_video.size

    ass_file, _ = create_ass_subtitles(final_content, video_width, video_height)

    original_duration = background_video.duration
    if final_duration > original_duration:
        num_repeats = int(final_duration // original_duration) + 1
        repeated_clips = [background_video] * num_repeats
        background_video = concatenate_videoclips(repeated_clips).subclip(0, final_duration)
    else:
        if original_duration > final_duration:
            start_time = random.uniform(0, original_duration - final_duration)
            background_video = background_video.subclip(start_time, start_time + final_duration)
        background_video = background_video.set_duration(final_duration)

    temp_video_file = "temp_background.mp4"
    background_video.write_videofile(temp_video_file, codec="libx264", audio=False, logger=None)

    audio_clips = []
    current_position = 0
    intro_audio_file = "reddit_asks_audio.mp3"
    if os.path.exists(intro_audio_file):
        intro_audio = AudioFileClip(intro_audio_file).set_start(current_position)
        audio_clips.append(intro_audio)
        current_position += intro_audio.duration + 1

    for post in final_content:
        title_audio_file = post.get('title_audio_file', f"title_audio_{current_position}.mp3")
        if os.path.exists(title_audio_file):
            title_audio = AudioFileClip(title_audio_file).set_start(current_position)
            audio_clips.append(title_audio)
            current_position += title_audio.duration + 1

        for comment in post.get('top_comments', []):
            author_audio_file = f"author_audio_{current_position}.mp3"
            if os.path.exists(author_audio_file):
                author_audio = AudioFileClip(author_audio_file)
                author_audio = author_audio.set_start(current_position)
                audio_clips.append(author_audio)
                current_position += author_audio.duration

            audio_file = comment.get('audio_file')
            if audio_file and os.path.exists(audio_file):
                audio_clip = AudioFileClip(audio_file).set_start(current_position)
                audio_clips.append(audio_clip)
                current_position += audio_clip.duration + 1

    final_audio = CompositeAudioClip(audio_clips)
    temp_audio_file = "temp_audio.mp3"
    final_audio.write_audiofile(temp_audio_file, fps=44100, logger=None)

    final_output_file = f"final_{output_file}"
    ffmpeg_command = (
        f"ffmpeg -i {temp_video_file} -i {temp_audio_file} -vf \"ass={ass_file}\" "
        f"-c:v libx264 -c:a aac -shortest {final_output_file} -y"
    )
    subprocess.run(ffmpeg_command, shell=True, check=True)

    os.remove(temp_video_file)
    os.remove(temp_audio_file)
    background_video.close()
    final_audio.close()

    print(f"Video created successfully: {final_output_file}")
    print(f"Duration: {datetime.timedelta(seconds=int(final_duration))}")
    #files.download(final_output_file)

    return True, final_content

def list_reddit_json_files():
    """List all available Reddit JSON data files."""
    json_files = list(Path('.').glob('reddit_top_posts_comments/top_posts_comments_*.json'))
    if not json_files:
        print("No Reddit data JSON files found. Please run the Reddit TTS script first.")
        return []
    for i, file in enumerate(sorted(json_files, key=os.path.getctime, reverse=True)):
        timestamp = os.path.getctime(file)
        time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{i+1}. {file} (Created: {time_str})")
    return sorted(json_files, key=os.path.getctime, reverse=True)

def main():
    """Main function to create video from Reddit TTS data."""
    print("===== Reddit TTS Video Creator =====")
    print("\nAvailable Reddit data files:")
    json_files = list_reddit_json_files()
    if not json_files:
        return False, None, None

    json_file = str(json_files[0])
    print(f"\nUsing most recent JSON file: {json_file}")

    with open(json_file, 'r', encoding='utf-8') as f:
        reddit_data = json.load(f)
    max_possible_duration = calculate_content_duration(reddit_data)
    print(f"Maximum possible video duration: {datetime.timedelta(seconds=int(max_possible_duration))}")

    target_duration=70
    #while True:
    #    try:
    #        target_duration = float(input("Enter desired video length in seconds (e.g., 60 for 1 minute): "))
    #        if 0 < target_duration <= max_possible_duration:
    #            break
    #        else:
    #            print(f"Please enter a value between 1 and {int(max_possible_duration)} seconds.")
    #    except ValueError:
    #        print("Please enter a valid number.")

    minecraft_videos = find_minecraft_videos("/content/drive/MyDrive/YouTUBE REDDIT/minecraft_videos")
    if not minecraft_videos:
        print("\nNo Minecraft videos found. Please upload one.")
        background_video_path = upload_minecraft_video()
        if not background_video_path:
            return False, None, None
    else:
        background_video_path = random.choice(minecraft_videos)
        print(f"\nUsing background video: {background_video_path}")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"reddit_minecraft_video_{timestamp}.mp4"

    success, final_content = create_video_with_subtitles(json_file, background_video_path, target_duration, output_file)
    return success, output_file, final_content

if __name__ == "__main__":
    success, output_file, final_content = main()
    if success:
        print(f"Final content used in video: {json.dumps(final_content, indent=2)}")
