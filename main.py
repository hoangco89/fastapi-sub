from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="YouTube Subtitle API",
    description="API lấy phụ đề YouTube theo URL hoặc video_id",
    version="1.0.0"
)

# Bật CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi domain gọi API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_video_id(url: str):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if "v" in query:
        return query["v"][0]

    if parsed.netloc in ["youtu.be"]:
        return parsed.path.lstrip("/")

    if "/embed/" in parsed.path:
        return parsed.path.split("/embed/")[-1]

    if len(url) == 11:
        return url

    return None

@app.get("/")
def home():
    return {"message": "FastAPI Subtitle Server is running!"}

@app.get("/subtitle")
def get_sub(url: str):
    video_id = extract_video_id(url)

    if not video_id:
        raise HTTPException(status_code=400, detail="Không lấy được video_id từ URL")

    try:
        subs = YouTubeTranscriptApi.get_transcript(video_id)
        return {"video_id": video_id, "subtitles": subs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
