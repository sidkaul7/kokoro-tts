from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import os
import uuid
from datetime import datetime, timedelta
import subprocess
import sys
from pathlib import Path
from moviepy.editor import VideoFileClip
import json

app = FastAPI()

# AWS Configuration
s3_client = boto3.client('s3', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
BUCKET_NAME = "wsobucket1"  # Your S3 bucket name
TABLE_NAME = "wso_metadata"  # Replace with your table name

class VideoRequest(BaseModel):
    title: str
    content: str

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
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', script_name)
    
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
        kokoro_dir = os.path.dirname(os.path.abspath(__file__))
        for file_pattern in check_files:
            # Get the most recent file matching the pattern
            if file_pattern.startswith("word_level_") or file_pattern.endswith(".wav"):
                search_dir = os.path.join(kokoro_dir, "last")
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

def generate_presigned_url(bucket, key, expiration=3600):
    """Generate a presigned URL for an S3 object."""
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        return response
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None

@app.post("/generate-video")
async def generate_video(request: VideoRequest):
    try:
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())
        
        # Save the request data to a JSON file
        json_path = os.path.join(os.path.dirname(__file__), 'wso_content.json')
        with open(json_path, 'w') as f:
            json.dump({
                'title': request.title,
                'content': request.content
            }, f)
        
        # Step 1: Run format_json.py (already done by saving the JSON)
        
        # Step 2: Run auto_tts.py
        if not run_script("auto_tts.py", check_files=[
            "word_level_*.srt",
            "*.wav"
        ]):
            raise HTTPException(status_code=500, detail="TTS generation failed")
        
        # Step 3: Run create_final_video.py
        final_video_path = run_script("create_final_video.py", check_files=[
            "final_video_*.mp4"
        ])
        if not final_video_path:
            raise HTTPException(status_code=500, detail="Video creation failed")
        
        # Check video duration
        duration = get_video_duration(final_video_path)
        if duration is None:
            raise HTTPException(status_code=500, detail="Could not determine video duration")
        
        # Upload the full video to S3
        full_video_key = f"videos/{request_id}/full_video.mp4"
        s3_client.upload_file(final_video_path, BUCKET_NAME, full_video_key)
        
        # Generate presigned URL for full video
        full_video_url = generate_presigned_url(BUCKET_NAME, full_video_key)
        
        # Store metadata in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        metadata = {
            'request_id': request_id,
            'title': request.title,
            'content': request.content,
            'duration': str(duration),  # Convert float to string for DynamoDB
            'created_at': datetime.utcnow().isoformat(),
            'full_video_key': full_video_key,
            'parts': []
        }
        
        # If video is longer than 120 seconds, split it
        if duration > 120:
            if not run_script("split_video.py", check_files=[
                "final_video_*_part*.mp4"
            ]):
                raise HTTPException(status_code=500, detail="Video splitting failed")
            
            # Upload split parts to S3 and generate presigned URLs
            parts = []
            for part_file in Path(os.path.dirname(final_video_path)).glob("final_video_*_part*.mp4"):
                part_key = f"videos/{request_id}/parts/{part_file.name}"
                s3_client.upload_file(str(part_file), BUCKET_NAME, part_key)
                part_url = generate_presigned_url(BUCKET_NAME, part_key)
                parts.append({
                    'key': part_key,
                    'url': part_url
                })
            
            metadata['parts'] = parts
        
        # Save metadata to DynamoDB
        table.put_item(Item=metadata)
        
        # Return the response
        return {
            'request_id': request_id,
            'duration': duration,
            'full_video_url': full_video_url,
            'parts': metadata['parts'] if duration > 120 else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 