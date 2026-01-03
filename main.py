from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

app = FastAPI(
    title="YouTube Subtitle API",
    description="API lấy phụ đề YouTube theo URL hoặc video_id",
    version="1.0.0"
)

# -----------------------------
# Hàm tách video_id an toàn
# -----------------------------
def extract_video_id(url: str):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    # Case 1: https://www.youtube.com/watch?v=ID
    if "v" in query:
        return query["v"][0]

    # Case 2: https://youtu.be/ID
    if parsed.netloc in ["youtu.be"]:
        return parsed.path.lstrip("/")

    # Case 3: https://www.youtube.com/embed/ID
    if "/embed/" in parsed.path:
        return parsed.path.split("/embed/")[-1]

    # Case 4: Người dùng gửi thẳng video_id
    if len(url) == 11:
        return url

    return None


# -----------------------------
# Route mặc định
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "FastAPI Subtitle Server is running!",
        "usage": "/subtitle?url=YOUTUBE_URL"
    }


# -----------------------------
# API lấy phụ đề
# -----------------------------
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
        