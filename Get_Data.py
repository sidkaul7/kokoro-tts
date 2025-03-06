# @title Get Data w TTS from Reddit

import praw
import pandas as pd
import datetime
import time
import os
import json
from datetime import timedelta
from gtts import gTTS  # Import Google Text-to-Speech
import mutagen.mp3  # For getting audio duration

def connect_to_reddit(client_id, client_secret, user_agent):
    """
    Connect to Reddit API using credentials
    """
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    return reddit

def get_top_posts_last_24h(reddit, subreddit_name, limit=10, min_score=50):
    """
    Retrieve top posts from a subreddit in the last 24 hours
    """
    twenty_four_hours_ago = datetime.datetime.utcnow() - timedelta(hours=24)
    twenty_four_hours_ago_timestamp = twenty_four_hours_ago.timestamp()
    subreddit = reddit.subreddit(subreddit_name)
    top_posts = []

    for post in subreddit.top(time_filter='day', limit=limit*3):
        if post.created_utc >= twenty_four_hours_ago_timestamp:
            post_data = {
                'id': post.id,
                'title': post.title,
                'score': post.score,
                'url': post.url,
                'permalink': post.permalink,
                'created_utc': datetime.datetime.fromtimestamp(post.created_utc).isoformat()
            }
            if post.score >= min_score:
                top_posts.append(post_data)
                if len(top_posts) >= limit:
                    break
    return top_posts

def get_audio_duration(audio_file):
    """
    Get the duration of an audio file in seconds
    """
    try:
        audio = mutagen.mp3.MP3(audio_file)
        return audio.info.length
    except Exception as e:
        print(f"Error getting duration for {audio_file}: {e}")
        return None

def get_top_comments_for_posts(reddit, posts, top_comments_per_post=5, min_comment_score=10, output_dir='reddit_top_posts_comments'):
    """
    Get top comments for each post and generate TTS audio files
    """
    posts_with_comments = []
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

    for post in posts:
        try:
            submission = reddit.submission(id=post['id'])
            submission.comments.replace_more(limit=0)
            submission.comment_sort = 'top'
            comment_data = []

            for comment in submission.comments:
                if comment.score >= min_comment_score:
                    comment_info = {
                        'id': comment.id,
                        'author': str(comment.author),
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': datetime.datetime.fromtimestamp(comment.created_utc).isoformat(),
                        'audio_file': None,  # Placeholder for audio file path
                        'audio_duration': None  # Placeholder for audio duration
                    }
                    # Generate TTS for this comment
                    try:
                        tts = gTTS(text=comment.body, lang='en')
                        audio_file = os.path.join(output_dir, f"comment_{comment.id}.mp3")
                        tts.save(audio_file)

                        # Get audio duration
                        duration = get_audio_duration(audio_file)

                        comment_info['audio_file'] = audio_file
                        comment_info['audio_duration'] = duration

                        print(f"Generated audio for comment {comment.id}: {audio_file} (Duration: {duration:.2f}s)")
                    except Exception as e:
                        print(f"Error generating TTS for comment {comment.id}: {e}")

                    comment_data.append(comment_info)

            top_comments = sorted(comment_data, key=lambda x: x['score'], reverse=True)[:top_comments_per_post]
            post_with_comments = post.copy()
            post_with_comments['top_comments'] = top_comments
            posts_with_comments.append(post_with_comments)
            time.sleep(0.5)  # Avoid rate limiting

        except Exception as e:
            print(f"Error processing post {post['id']}: {e}")
            continue

    return posts_with_comments

def save_results(data, output_dir='reddit_top_posts_comments', format='json'):
    """
    Save results to file
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if format.lower() == 'json':
        file_path = os.path.join(output_dir, f'top_posts_comments_{timestamp}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    elif format.lower() == 'csv':
        file_path = os.path.join(output_dir, f'top_posts_comments_{timestamp}.csv')
        flat_data = []
        for post in data:
            base_post = post.copy()
            top_comments = base_post.pop('top_comments', [])
            if top_comments:
                for i, comment in enumerate(top_comments, 1):
                    flat_post = base_post.copy()
                    flat_post.update({
                        f'comment{i}_id': comment['id'],
                        f'comment{i}_author': comment['author'],
                        f'comment{i}_score': comment['score'],
                        f'comment{i}_body': comment['body'][:200],
                        f'comment{i}_audio': comment.get('audio_file', 'N/A'),
                        f'comment{i}_duration': comment.get('audio_duration', 'N/A')
                    })
                    flat_data.append(flat_post)
            else:
                flat_data.append(base_post)
        pd.DataFrame(flat_data).to_csv(file_path, index=False)
    else:
        raise ValueError(f"Invalid format: {format}")

    print(f"Saved results to {file_path}")
    return file_path

def format_duration(seconds):
    """
    Format duration in seconds to a readable time format (MM:SS)
    """
    if seconds is None:
        return "N/A"

    minutes = int(seconds) // 60
    remaining_seconds = int(seconds) % 60
    return f"{minutes}:{remaining_seconds:02d}"

def main(client_id, client_secret, subreddit_name,
         user_agent='TopPostsComments/1.0',
         posts_limit=10,
         min_post_score=50,
         top_comments_per_post=5,
         min_comment_score=10,
         output_dir='reddit_top_posts_comments',
         format='json'):
    """
    Main function to retrieve top posts, comments, and generate TTS
    """
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)

    reddit = connect_to_reddit(client_id, client_secret, user_agent)
    top_posts = get_top_posts_last_24h(reddit, subreddit_name, limit=posts_limit, min_score=min_post_score)
    posts_with_comments = get_top_comments_for_posts(reddit, top_posts, top_comments_per_post, min_comment_score, output_dir)
    save_results(posts_with_comments, output_dir, format)

    return posts_with_comments

if __name__ == "__main__":
    CLIENT_ID = "xxx"
    CLIENT_SECRET = "xxx"
    SUBREDDIT_NAME = "AskReddit"

    results = main(
        CLIENT_ID,
        CLIENT_SECRET,
        SUBREDDIT_NAME,
        posts_limit=3,
        min_post_score=500,
        top_comments_per_post=4,
        min_comment_score=100,
        format='json'
    )

    for post in results:
        print(f"Post: {post['title']} (Upvotes: {post['score']})")
        print("Top Comments:")
        for comment in post.get('top_comments', []):
            duration_str = format_duration(comment.get('audio_duration'))
            print(f"  - Score: {comment['score']}, Author: {comment['author']}, Audio: {comment.get('audio_file', 'N/A')}, Duration: {duration_str}")
        print("\n")
