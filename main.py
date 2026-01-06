from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import requests
import re

app = FastAPI()

# Cho phép mọi trình duyệt gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def extract_simple_json(sub_json):
    """Chuyển JSON phụ đề YouTube sang dạng [{start, end, text}]"""
    items = []
    events = sub_json.get("events", [])

    for ev in events:
        if "segs" not in ev:
            continue

        start = ev.get("tStartMs", 0) / 1000
        end = start + ev.get("dDurationMs", 0) / 1000
        text = "".join(seg.get("utf8", "") for seg in ev["segs"]).strip()

        if text:
            items.append({
                "start": round(start, 3),
                "end": round(end, 3),
                "text": text,
                "textdich": ""

            })

    return items


@app.get("/subtitle")
def get_subtitle(url: str = Query(...), lang: str = "en"):
    """
    API: /subtitle?url=YOUTUBE_URL&lang=en
    Trả về phụ đề dạng [{start, end, text, textdich}]
    """

    # Lấy metadata video
    meta_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(meta_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = sanitize_filename(info.get("title", "subtitle"))

    # Lấy phụ đề
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "json",
        "subtitleslangs": [lang],
        "quiet": True,
        'no_warnings': True,
        'ratelimit': 500000,  # giới hạn tốc độ tải: 500 KB/s
        'sleep_interval_requests': 2,  # nghỉ 2 giây giữa các request
        'forcejson': True

    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(url, download=False)

    subs = data.get("subtitles") or data.get("automatic_captions")

    if not subs or lang not in subs:
        return {"error": "Không tìm thấy phụ đề cho video này."}

    # URL phụ đề JSON
    sub_url = subs[lang][0]["url"]
    raw_json = requests.get(sub_url).json()

    # Chuyển sang dạng đơn giản
    simple_json = extract_simple_json(raw_json)

    return {
        "title": title,
        "lang": lang,
        "count": len(simple_json),
        "subtitles": simple_json
    }
