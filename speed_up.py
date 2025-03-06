# @title Speed up the Video (Optional)

from moviepy.editor import VideoFileClip, vfx

def speed_up_video(input_path, output_path, speed_factor):
    try:
        # Load the video file
        video = VideoFileClip(input_path)

        # Apply speed effect (speed_factor > 1 speeds up, < 1 slows down)
        # For example, 2.0 = 2x faster, 0.5 = half speed
        sped_up_video = video.fx(vfx.speedx, speed_factor)

        # Write the output file
        sped_up_video.write_videofile(
            output_path,
            codec="libx264",        # Video codec
            audio_codec="aac",      # Audio codec
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            verbose=True
        )

        print(f"Video successfully processed and saved to {output_path}")

        # Close the video objects to free up memory
        video.close()
        sped_up_video.close()

    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Specify your input and output file paths
    print("Video path")
    input_file = f"final_{output_file}" #str(input())#"/content/final_reddit_minecraft_video_20250305_223744.mp4"    # Replace with your input video path
    output_file_sp = "output_sped_up.mp4" # Desired output path
    print("===== Speed Up Video =====")
    speed = 1.10#float(input())#1.25                       # Speed factor (2x faster)

    speed_up_video(input_file, output_file_sp, speed)
