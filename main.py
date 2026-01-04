from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
import tempfile
import os

app = FastAPI(
    title="YouTube Subtitle API (yt-dlp version)",
    description="Lấy phụ đề YouTube bằng yt-dlp, không bị chặn 429",
    version="1.0.0"
)

# Bật CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API chạy bằng yt-dlp, ổn định và không bị chặn!"}

@app.get("/subtitle")
def get_sub(url: str):
    try:
        # Tạo file tạm để yt-dlp lưu phụ đề JSON
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subtitles")

            cmd = [
                "yt-dlp",
                "--write-auto-subs",          # lấy phụ đề auto
                "--sub-format", "json",       # định dạng JSON
                "--skip-download",            # không tải video
                "-o", output_path,            # đường dẫn output
                url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # Kiểm tra lỗi yt-dlp
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=result.stderr)

            # Tìm file phụ đề JSON
            for file in os.listdir(tmpdir):
                if file.endswith(".json"):
                    with open(os.path.join(tmpdir, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return data

            raise HTTPException(status_code=404, detail="Không tìm thấy phụ đề JSON")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        