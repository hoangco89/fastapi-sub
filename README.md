# FastAPI Subtitle API

API lấy phụ đề YouTube từ URL hoặc video_id.

## Cách chạy local
pip install -r requirements.txt uvicorn main:app --reload


Mở trình duyệt:
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/docs

## Deploy lên Render

- Push code lên GitHub
- Tạo Web Service mới
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Gọi API
GET /subtitle?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
