from fastapi import FastAPI, HTTPException
from yt_dlp import YoutubeDL
import requests
import xml.etree.ElementTree as ET
import re

app = FastAPI()

def parse_time(t):
    if t is None:
        return None
    t = t.strip()

    if re.match(r"^\d{2}:\d{2}:\d{2}(\.\d+)?$", t):
        h, m, s = t.split(":")
        return int(h)*3600 + int(m)*60 + float(s)

    if re.match(r"^\d{2}:\d{2}(\.\d+)?$", t):
        m, s = t.split(":")
        return int(m)*60 + float(s)

    if t.endswith("s"):
        return float(t[:-1])

    if t.endswith("ms"):
        return float(t[:-2]) / 1000

    try:
        return float(t)
    except:
        return None


def ttml_text_to_json(ttmlText):
    root = ET.fromstring(ttmlText)

    ns = {}
    if root.tag.startswith("{"):
        uri = root.tag.split("}")[0].strip("{")
        ns["tt"] = uri

    p_elems = root.findall(".//tt:p", ns) if ns else root.findall(".//p")

    result = []
    for p in p_elems:
        begin = parse_time(p.get("begin"))
        end = parse_time(p.get("end"))
        dur = parse_time(p.get("dur"))

        if begin is not None and end is None and dur is not None:
            end = begin + dur

        text = "".join(p.itertext()).strip()

        if begin is not None and end is not None and text:
            result.append({
                "start": round(begin, 3),
                "end": round(end, 3),
                "text": text
            })

    return result


@app.get("/")
def home():
    return {"message": "YouTube Subtitle API is running!"}


@app.get("/subtitle")
def get_subtitle(url: str, lang: str = "en"):
    try:
        ydl_opts = {"skip_download": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        subs = info.get("automatic_captions", {}).get(lang, [])

        entry = next((s for s in subs if s.get("ext") == "ttml"), None)

        if not entry:
            raise HTTPException(404, "Không tìm thấy phụ đề TTML")

        sub_url = entry["url"]
        ttml_text = requests.get(sub_url).text

        data = ttml_text_to_json(ttml_text)
        return data

    except Exception as e:
        raise HTTPException(500, f"Lỗi: {str(e)}")
        