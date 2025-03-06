# 🚀 Fully Automated YouTube Channel

https://github.com/user-attachments/assets/780c6222-2d33-47ad-8dc2-4fe92634332d



Welcome to my **Fully Automated YouTube Channel** project! Launched on **March 05, 2025**, this system creates and uploads a new 1-minute video to YouTube every day, completely hands-free. It gathers content from Reddit (default: **AskReddit**), generates narrated videos with Minecraft gameplay backgrounds, optimizes them with SEO, and uploads them automatically. Below, you’ll find an overview, features, and setup instructions!

---

## 🚀 Project Overview

This project automates video content creation using a pipeline of Python scripts:

1. **`get_data.py`**: Scrapes top posts and comments from AskReddit (last 24 hours), generates TTS audio for titles and comments, and saves data as JSON.
2. **`create_videos.py`**: Combines TTS audio with a Minecraft background video, adds ASS subtitles, and produces a 1-minute video (Google Colab compatible).
3. **`speed_up.py`**: Optionally adjusts video speed (e.g., 1.1x) for a snappier feel.
4. **SEO & Upload Script**: Uses OpenAI’s GPT-4o-mini to generate SEO-optimized titles, keywords, and descriptions, then uploads the video to YouTube via a custom script.

The result? A **100% automated** YouTube channel posting daily videos with no manual effort—once you set up the automation!

---

## 🎥 Features

- **Reddit Integration**: Pulls top posts (min score: 500) and comments (min score: 100) from AskReddit, customizable to any subreddit.
- **TTS Narration**: Uses Google Text-to-Speech (gTTS) for post titles and comments, prefixed with “Reddit Asks” and “User says.”
- **Minecraft Background**: Adds gameplay footage (e.g., from `/minecraft_videos/`), replayed or trimmed to fit the ~70-second target duration.
- **Subtitles**: Generates ASS-format subtitles for accessibility and engagement, styled in yellow with black outlines.
- **Speed Adjustment**: Optional speed-up (e.g., 1.1x) using MoviePy for a polished pace.
- **SEO Optimization**: Leverages OpenAI’s GPT-4o-mini for catchy titles, keywords, and descriptions.
- **Daily Uploads**: Automatically uploads to YouTube with public visibility (category: Entertainment).
- **Open Source**: Full code available, including a Google Colab notebook for easy testing.

---

## 🛠️ How It Works

1. **Data Collection**: `get_data.py` connects to Reddit via PRAW, fetches top posts/comments, and generates TTS audio files.
2. **Video Creation**: `create_videos.py` selects content to fit ~70 seconds, layers it with Minecraft footage, adds subtitles, and exports the video.
3. **Speed Adjustment**: `speed_up.py` (optional) speeds up the video for a tighter runtime.
4. **SEO & Upload**: The final script generates SEO metadata and uploads the video using a custom YouTube API script.

Run it manually, or set up your own system to automate it daily (see "Get Started" below).

---

## 📚 Resources

- **Google Colab Notebook**: [Coming Soon](#) – Run the full pipeline in the cloud.
- **GitHub Code**: All scripts are here in this repository.
- **Udemy Course**: Learn more in my [Udemy course](#) (link TBD).
- **YouTube Channel**: See sample videos on my [YouTube channel](#) (link TBD).

---

## 💡 Example

Here’s a sample video created by this project:
- **Source**: Top AskReddit posts and comments (e.g., score > 500/100).
- **Narration**: “Reddit Asks” + post title, “User says” + top comments.
- **Background**: Minecraft gameplay from `/minecraft_videos/`.
- **Subtitles**: Yellow text near the bottom.
- **Duration**: ~70 seconds (adjustable).
- **SEO**: “What’s the Wildest Reddit Ask? Minecraft Reddit Stories” with tags like “reddit stories, minecraft, askreddit.”

---

## 🏁 Get Started

### Prerequisites
- Python 3.8+
- Reddit API credentials (`client_id`, `client_secret`, `user_agent`) (Create an app here https://www.reddit.com/prefs/apps)
- YouTube API credentials for uploads (how to get one: https://www.youtube.com/watch?v=aFwZgth790Q&t)
- OpenAI API key for SEO
- Minecraft gameplay video (`.mp4`, etc.)
- Dependencies: `praw`, `gTTS`, `moviepy`, `pysubs2`, `openai`, `ffmpeg`, etc. (see `requirements.txt`)

