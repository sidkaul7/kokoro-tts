import os
import json
import sys
from pathlib import Path

# Add parent directory to path to import from app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import KOKORO_TTS_API

def process_tts(title, content):
    """Process TTS directly using the Kokoro API."""
    # Combine title and content with double newline and add a small buffer at the end
    full_text = f"{title}\n\n{content}\n\n"  # Extra newlines at the end to ensure all words are spoken
    
    print("\nProcessing TTS...")
    print(f"Total text length: {len(full_text)} characters")
    
    # Call the TTS API directly with adjusted speed for longer content
    audio_path, _, word_level_srt, _, _ = KOKORO_TTS_API(
        text=full_text,
        Language="American English",
        voice="af_bella",
        speed=1.0,  # Slightly slower speed to ensure all words are spoken
        translate_text=False,
        remove_silence=False
    )
    
    print(f"\nAudio generated: {audio_path}")
    print(f"Word-level SRT generated: {word_level_srt}")
    return True

def main():
    print("Reading content from wso_content.json...")
    
    # Read the JSON file
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wso_content.json')
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    title = data['title']
    content = data['content']
    
    print(f"Title length: {len(title)}")
    print(f"Content length: {len(content)}")
    print(f"First 100 chars of content: {content[:100]}")
    print(f"Last 100 chars of content: {content[-100:]}")
    
    print(f"Processing TTS for title: {title}")
    if not process_tts(title, content):
        print("Error: TTS processing failed")
        sys.exit(1)
    print("TTS processing completed successfully!")

if __name__ == "__main__":
    main() 