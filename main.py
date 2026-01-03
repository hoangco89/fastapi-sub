from fastapi import FastAPI
from youtube_transcript_api import YouTubeTranscriptApi

app = FastAPI()

@app.get("/subtitle")
def get_sub(url: str):
    video_id = url.split("v=")[-1]
    subs = YouTubeTranscriptApi.get_transcript(video_id)
    return subs
