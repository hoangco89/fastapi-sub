# streamlit_app.py - Hỏi đáp với Groq: gõ hoặc nói, trả lời bằng chữ + giọng đọc
import io
import re

import requests
import streamlit as st
from gtts import gTTS

st.set_page_config(page_title="Q&A with Groq")
st.header("Q&A with Groq AI")

# ---------- Cổng mật khẩu (chỉ bật nếu có APP_PASSWORD trong Secrets) ----------
pw_required = st.secrets.get("APP_PASSWORD")
if pw_required and not st.session_state.get("ok"):
    pw = st.text_input("Password", type="password")
    if pw:
        if pw == pw_required:
            st.session_state.ok = True
            st.rerun()
        else:
            st.error("Sai mật khẩu.")
    st.stop()

# ---------- Cấu hình ----------
API_KEY = st.secrets.get("GROQ_API_KEY")
MODEL = st.secrets.get("GROQ_MODEL", "qwen/qwen3.8-27b")
STT_MODEL = st.secrets.get("GROQ_STT_MODEL", "whisper-large-v3-turbo")

if not API_KEY:
    st.error("Thiếu GROQ_API_KEY trong Secrets.")
    st.stop()

GROQ = "https://api.groq.com/openai/v1"
LANGS = {"English": "en", "Vietnamese": "vi", "French": "fr", "Denmark": "da", "Chinese": "zh"}

if "history" not in st.session_state:
    st.session_state.history = []


# ---------- Các hàm ----------
def transcribe(wav_bytes, lang):
    """Giọng nói -> chữ bằng Whisper trên Groq."""
    r = requests.post(
        f"{GROQ}/audio/transcriptions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"file": ("voice.wav", wav_bytes, "audio/wav")},
        data={"model": STT_MODEL, "language": lang, "response_format": "json"},
        timeout=60,
    )
    body = r.json()
    if not r.ok:
        raise RuntimeError(body.get("error", {}).get("message", "Lỗi nhận diện giọng nói."))
    return body.get("text", "").strip()


def ask_groq(history):
    r = requests.post(
        f"{GROQ}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "max_tokens": 500,
            "messages": [
                {"role": "system", "content": "Bạn là trợ lý hữu ích. Trả lời ngắn gọn, rõ ràng, bằng ngôn ngữ của người hỏi."},
                *history,
            ],
        },
        timeout=60,
    )
    body = r.json()
    if not r.ok:
        raise RuntimeError(body.get("error", {}).get("message", "Lỗi từ Groq."))
    return body["choices"][0]["message"]["content"]


def text_to_speech(text, lang):
    """Chữ -> file mp3 bằng gTTS."""
    clean = re.sub(r"[*#`_>~]", "", text)
    buf = io.BytesIO()
    gTTS(clean, lang=lang).write_to_fp(buf)
    return buf.getvalue()


# ---------- Giao diện ----------
CHAT_HEIGHT = 300  # 420 chiều cao khung chat (px), chỉnh theo màn hình của bạn

c1, c2 = st.columns(2)
lang_name = c1.selectbox(":blue[Ngôn ngữ]", list(LANGS))
lang = LANGS[lang_name]
read_aloud = c2.toggle("Đọc câu trả lời", value=True)

# Khung chat có chiều cao cố định, nội dung dài sẽ cuộn bên trong khung
chat_box = st.container(height=CHAT_HEIGHT, border=True)

# MỘT ô duy nhất: gõ chữ hoặc bấm biểu tượng micro để nói (cần Streamlit >= 1.50)
prompt = st.chat_input("Gõ câu hỏi hoặc bấm 🎤 để nói...", accept_audio=True)

# Hiện lịch sử trong khung
with chat_box:
    for m in st.session_state.history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# Lấy chữ và/hoặc âm thanh từ ô nhập
question = None
if prompt:
    if isinstance(prompt, str):
        text, audio = prompt, None
    else:
        text, audio = prompt.get("text"), prompt.get("audio")

    if text and text.strip():
        question = text.strip()  # có gõ chữ thì ưu tiên chữ
    elif audio is not None:
        with st.spinner("Đang nhận diện giọng nói..."):
            try:
                question = transcribe(audio.getvalue(), lang) or None
                if not question:
                    st.warning("Không nghe rõ, hãy thử lại.")
            except Exception as e:
                st.error(f"Lỗi nhận diện giọng nói: {e}")

if question:
    st.session_state.history.append({"role": "user", "content": question})
    with chat_box:  # câu hỏi và câu trả lời mới cũng hiện trong khung
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Đang suy nghĩ..."):
                try:
                    reply = ask_groq(st.session_state.history)
                    st.markdown(reply)
                    st.session_state.history.append({"role": "assistant", "content": reply})
                    if read_aloud:
                        try:
                            st.audio(text_to_speech(reply, lang), format="audio/mp3", autoplay=True)
                        except Exception as e:
                            st.caption(f"Không đọc được câu trả lời: {e}")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
                    st.session_state.history.pop()
