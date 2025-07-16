# streamlit run app.py

import streamlit as st
from audiorecorder import audiorecorder
import requests
import io

FASTAPI_BASE = "http://localhost:8000"

def login_form():
    st.title("Đăng nhập")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        r = requests.post(f"{FASTAPI_BASE}/login", json={
            "username": username, "password": password
        })
        if r.status_code == 200:
            st.session_state["logged_in"] = True
            st.success("Đăng nhập thành công!")
            st.rerun()
        else:
            st.error("Sai tên đăng nhập hoặc mật khẩu")

def record_audio():
    st.header("Ghi âm/Upload audio, chuyển thành hình ảnh")
    st.info("Nhấn ghi âm, dừng lại rồi nhấn các nút bên dưới")
    audio_segment = audiorecorder()
    audio_bytes = None

    if audio_segment is not None:
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format='wav')
        audio_bytes = wav_io.getvalue()
        st.audio(audio_bytes, format="audio/wav")

    if audio_bytes and st.button("Chuyển thành văn bản"):
        files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
        r = requests.post(f"{FASTAPI_BASE}/speech2text", files=files)
        if r.status_code == 200:
            response = r.json()
            # Thiết lập giá trị khởi tạo cho text_area trong session, để cho phép sửa
            st.session_state["asr_text"] = response["text"]
            st.session_state["audio_url"] = response.get("audio_file", "")
            st.session_state["tokens"] = response.get("tokens", "")
            st.session_state["text_ready"] = True
            st.rerun()
        else:
            st.error("Lỗi nhận diện giọng nói!")

    if st.session_state.get('text_ready', False):
        asr_text = st.text_area("Văn bản nhận diện", value=st.session_state["asr_text"])
        if st.button("Sinh ảnh từ văn bản đã sửa"):
            r2 = requests.post(
                f"{FASTAPI_BASE}/text2image",
                data={"text": asr_text}
            )
            if r2.status_code == 200:
                img_url = r2.json()["image_url"]
                st.image(FASTAPI_BASE + img_url)
            else:
                st.error("Không sinh được ảnh")

        # Nút trở lại nếu muốn làm lại quá trình
        if st.button("Ghi âm lại/làm mới"):
            st.session_state["text_ready"] = False
            st.session_state["asr_text"] = ""
            st.session_state["audio_url"] = ""
            st.session_state["tokens"] = ""
            st.rerun()

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if st.session_state["logged_in"]:
        record_audio()
    else:
        login_form()

if __name__ == '__main__':
    main()