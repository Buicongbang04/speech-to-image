# uvicorn app:app --reload

import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ==== Tạo folder nếu chưa có ====
AUDIO_DIR = "audio"
IMAGES_DIR = "images"
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# ==== Init FastAPI ====
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# ==== Dummy users for login ====
users = {"admin": "123456", "user": "123"}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginRequest):
    if data.username in users and users[data.username] == data.password:
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Sai username/password")

# ====== PhoBERT: Load tokenizer/model ======
print("▶ Đang tải PhoBERT (vinai/phobert-large)...")
import torch
from transformers import AutoTokenizer, AutoModel

PHOBERT_TOKENIZER = AutoTokenizer.from_pretrained("vinai/phobert-large")
PHOBERT_MODEL = AutoModel.from_pretrained("vinai/phobert-large")
print("✓ Đã tải PhoBERT")

# ====== Stable Diffusion: runwayml/stable-diffusion-v1-5 ======
print("▶ Đang tải Stable Diffusion (runwayml/stable-diffusion-v1-5)...")
from diffusers import StableDiffusionPipeline

SD_MODEL_ID = "runwayml/stable-diffusion-v1-5"
sd_pipe = StableDiffusionPipeline.from_pretrained(
    SD_MODEL_ID,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
)
if torch.cuda.is_available():
    sd_pipe = sd_pipe.to("cuda")
print("✓ Đã tải Stable Diffusion")

def generate_image_stable_diffusion(prompt: str):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    with torch.autocast(device):
        image = sd_pipe(prompt, num_inference_steps=30, guidance_scale=7.5).images[0]
    return image

# ====== ENDPOINT SPEECH2TEXT ======
@app.post("/speech2text")
async def speech2text(audio: UploadFile = File(...)):
    # 1. Lưu file audio
    audio_id = uuid.uuid4().hex
    audio_path = os.path.join(AUDIO_DIR, f"{audio_id}.wav")
    with open(audio_path, "wb") as f:
        audio_bytes = await audio.read()
        f.write(audio_bytes)
    # 2. Nhận dạng tiếng nói (Whisper)
    import whisper
    whisper_model = whisper.load_model("base")
    result = whisper_model.transcribe(audio_path, language="vi")
    text = result["text"]
    # 3. Xử lý với PhoBERT
    tokens = PHOBERT_TOKENIZER.tokenize(text)
    input_ids = PHOBERT_TOKENIZER.encode(text, return_tensors='pt')
    with torch.no_grad():
        features = PHOBERT_MODEL(input_ids)
    # Chỉ trả tokens (bạn mở rộng làm gì với feature vector tuỳ ý)
    return {
        "text": text,
        "tokens": tokens,
        "audio_file": f"/audio/{audio_id}.wav"
    }

# ====== ENDPOINT TEXT2IMAGE ======
@app.post("/text2image")
def text2image(text: str = Form(...)):
    img = generate_image_stable_diffusion(text)
    img_id = uuid.uuid4().hex
    img_path = os.path.join(IMAGES_DIR, f"{img_id}.png")
    img.save(img_path)
    return {"image_url": f"/images/{img_id}.png"}

# -------- END FILE ----------