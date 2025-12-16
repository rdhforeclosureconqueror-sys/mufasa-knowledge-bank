from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from openai import OpenAI
import requests
import os
import uuid
import logging

router = APIRouter()

# ==========================================================
# ⚙️ CONFIGURATION
# ==========================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIVOICE_BASE_URL = os.getenv("AIVOICE_BASE_URL", "https://aivoice-wmrv.onrender.com")
AIVOICE_API_KEY = os.getenv("AIVOICE_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://mufasa-knowledge-bank.onrender.com")

client = OpenAI(api_key=OPENAI_API_KEY)

# Logging setup
logger = logging.getLogger("mufasa-chat")
logger.setLevel(logging.INFO)


# ==========================================================
# 📦 HELPERS
# ==========================================================
def aivoice_headers() -> dict:
    """Attach security header for aiVoice calls."""
    return {"X-AIVOICE-KEY": AIVOICE_API_KEY} if AIVOICE_API_KEY else {}


def save_audio_file(content: bytes) -> str:
    """Save TTS audio locally and return public URL."""
    audio_filename = f"{uuid.uuid4()}.mp3"
    audio_path = f"app/static/audio/{audio_filename}"
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    with open(audio_path, "wb") as f:
        f.write(content)
    return f"{BASE_URL}/static/audio/{audio_filename}"


# ==========================================================
# 📩 SCHEMAS
# ==========================================================
class ChatRequest(BaseModel):
    message: str
    user_id: str = "guest"
    voice: bool = True


# ==========================================================
# 🧠 1️⃣ TEXT CHAT (with optional Voice)
# ==========================================================
@router.post("/message")
async def generate_openai_response(request: ChatRequest):
    """
    Text chat → (GPT reply) → optional aiVoice TTS.
    """
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Empty message not allowed.")

        logger.info(f"🗣 Incoming message: {request.message}")

        # --- Step 1: GPT reply ---
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the Pan-African AI historian and philosopher. "
                        "Speak with wisdom, confidence, and deep knowledge of African history, "
                        "heritage, and liberation movements. Inspire pride and unity."
                    ),
                },
                {"role": "user", "content": request.message},
            ],
            temperature=0.7,
        )
        ai_text = completion.choices[0].message.content.strip()
        logger.info(f"🦁 Mufasa replies: {ai_text}")

        # --- Step 2: Optional TTS via aiVoice ---
        audio_url = None
        if request.voice:
            try:
                tts_response = requests.post(
                    f"{AIVOICE_BASE_URL}/tts",
                    json={"text": ai_text, "format": "mp3"},
                    headers=aivoice_headers(),
                    timeout=60,
                )
                if tts_response.status_code == 200:
                    audio_url = save_audio_file(tts_response.content)
                    logger.info(f"🎵 Voice generated → {audio_url}")
                else:
                    logger.warning(
                        f"⚠️ aiVoice TTS failed ({tts_response.status_code}): {tts_response.text}"
                    )
            except Exception as ve:
                logger.error(f"🎤 Voice synthesis error: {ve}")

        return {"reply": ai_text, "audio_url": audio_url, "source": "MufasaKnowledgeBank"}

    except Exception as e:
        logger.error(f"❌ Chat API error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {e}")


# ==========================================================
# 🎙️ 2️⃣ VOICE CHAT (Speech → Text → Brain → Speech)
# ==========================================================
@router.post("/voice")
async def chat_with_voice(file: UploadFile = File(...)):
    """
    Full voice pipeline:
    1. Transcribe speech via aiVoice /whisper
    2. Generate GPT reply
    3. Convert reply to speech via aiVoice /tts
    """
    try:
        # --- Step 1: STT via aiVoice ---
        stt_response = requests.post(
            f"{AIVOICE_BASE_URL}/whisper",
            files={"file": (file.filename, await file.read(), file.content_type)},
            headers=aivoice_headers(),
            timeout=90,
        )
        stt_response.raise_for_status()
        transcript = stt_response.json().get("text", "").strip()
        if not transcript:
            raise Exception("Empty transcript returned from aiVoice")

        logger.info(f"🗣 Transcribed speech: {transcript}")

        # --- Step 2: Generate Mufasa's reply ---
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the Pan-African AI historian and philosopher. "
                        "Speak with power, warmth, and wisdom about Africa’s unity and greatness."
                    ),
                },
                {"role": "user", "content": transcript},
            ],
            temperature=0.7,
        )
        reply_text = completion.choices[0].message.content.strip()
        logger.info(f"🦁 Voice reply: {reply_text}")

        # --- Step 3: TTS via aiVoice ---
        tts_response = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json={"text": reply_text, "format": "mp3"},
            headers=aivoice_headers(),
            timeout=90,
        )
        tts_response.raise_for_status()
        audio_url = save_audio_file(tts_response.content)
        logger.info(f"🎧 Voice chat audio saved: {audio_url}")

        return {
            "transcript": transcript,
            "reply": reply_text,
            "audio_url": audio_url,
            "source": "MufasaKnowledgeBank",
        }

    except Exception as e:
        logger.error(f"❌ Voice chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {e}")


# ==========================================================
# 🩺 3️⃣ HEALTH CHECK
# ==========================================================
@router.get("/ping")
def ping():
    return {"ok": True, "message": "Mufasa Chat API is alive and roaring 🦁"}
