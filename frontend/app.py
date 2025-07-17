# streamlit run app.py

import streamlit as st
from audiorecorder import audiorecorder
import requests
import io
import base64

FASTAPI_BASE = "http://localhost:8000"

def login_form():
    def local_image_as_base64(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    bot_b64 = local_image_as_base64("image/bot.jpg")
    face_b64 = local_image_as_base64("image/facebook.png")
    google_b64 = local_image_as_base64("image/google.png")

    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #2a2cdb 0%, #5533ff 100%) fixed; }
        .login-panel {
            background: rgba(255,255,255,0.05);
            border-radius: 32px;
            margin: 40px auto 0 auto;
            width: 700px;
            display: flex;
            box-shadow: 0 20px 40px 0 rgba(32,37,76, 0.18);
        }
        .login-left {
            flex: 1 1 0%;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 32px 25px 32px 32px;
        }
        .login-left img {
            width: 220px;
            min-width: 180px;
            border-radius: 16px;
            background: none;
        }
        .login-right {
            flex: 1.2 1 0%;
            padding: 44px 36px;
            color: #fff;
            position: relative;
        }
        .login-right h1 {
            font-size: 2rem;
            margin-bottom: 10px;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
        .ai-icon {
            font-size: 2rem;
            background: linear-gradient(to right,#48c6ef, #6f86d6);
            padding: 6px 12px;
            border-radius: 12px;
            margin-right: 10px;
            color: #031f57;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="login-panel">
        <div class="login-left">
            <img src="data:image/jpg;base64,{bot_b64}" alt="ChatBot Icon">
        </div>
        <div class="login-right"">
            <h1>
                <span class="ai-icon">🤖</span>
                <span><span style="color:#48c6ef;">AI</span><span style="color:#fff;">STI</span></span>
            </h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align:center; margin-top: 20px;">
            <h2 style="color:#fff;">Đăng nhập vào hệ thống</h2>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form_st"):
        username = st.text_input("Username", key="username_css")
        password = st.text_input("Password", type="password", key="password_css")
        remember_me = st.checkbox("Remember Me", key="remember_css")
        submit_btn = st.form_submit_button("Sign In")
        if submit_btn:
            r = requests.post(f"{FASTAPI_BASE}/login", json={
                "username": username, "password": password
            })
            if r.status_code == 200:
                st.session_state["logged_in"] = True
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Sai tên đăng nhập hoặc mật khẩu")

    st.markdown(f"""
        <div class="info-links" style="margin-top:1.5rem;">
            New on our Platform?
            <a href="#"><b>Create an Account</b></a>
        </div>
        <div style="text-align:center; margin-top:10px; margin-bottom:8px;">or</div>
        <div class="form-socials" style="text-align:center;">
            <button class="social-btn" style="margin-right:12px; background:none; border:none; box-shadow:none;">
            <img src="data:image/png;base64,{face_b64}" alt="Facebook" 
                style="width:28px;height:28px;vertical-align:middle;">
            </button>
            <button class="social-btn" style="margin-right:12px; background:none; border:none; box-shadow:none;">
            <img src="data:image/png;base64,{google_b64}" alt="Google" 
                style="width:28px;height:28px;vertical-align:middle;">
            </button>
        </div>
    """, unsafe_allow_html=True)

def record_audio():
    st.header("Ghi âm/Upload audio, chuyển thành hình ảnh")
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