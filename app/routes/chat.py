from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import requests
import os
import uuid
import logging

# --------------------------
# 🔧 Setup and Configuration
# --------------------------
router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENVOICE_API_URL = os.getenv("OPENVOICE_API_URL")
BASE_URL = os.getenv("BASE_URL", "https://mufasa-knowledge-bank.onrender.com")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY not found. Please set it in Render environment variables.")

openai.api_key = OPENAI_API_KEY

# --------------------------
# 🪶 Logging
# --------------------------
logger = logging.getLogger("mufasa-chat")
logger.setLevel(logging.INFO)


# --------------------------
# 📦 Request Schema
# --------------------------
class ChatRequest(BaseModel):
    message: str
    user_id: str = "guest"
    voice: bool = True


# --------------------------
# 🧠 POST /chat/message
# --------------------------
@router.post("/message")
async def generate_openai_response(request: ChatRequest):
    """
    Handles chat messages from the Prince of Pan-Africa frontend.
    Returns Mufasa's text response and optional voice audio URL.
    """
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Empty message not allowed.")

        logger.info(f"🗣 Incoming message from {request.user_id}: {request.message}")

        # --- 1️⃣ Generate AI response ---
        try:
            completion = openai.chat.completions.create(
                model="gpt-4.1",  # Prefer GPT-4.1
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are Mufasa, the Pan-African AI historian and philosopher. "
                            "Speak with wisdom, pride, and reverence for African heritage. "
                            "Offer insight, clarity, and empowerment to your listeners."
                        ),
                    },
                    {"role": "user", "content": request.message},
                ],
                temperature=0.7,
            )
        except Exception as model_error:
            logger.warning(f"⚠️ GPT-4.1 unavailable, falling back to GPT-4o-mini: {model_error}")
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are Mufasa, Pan-African AI guide and philosopher."},
                    {"role": "user", "content": request.message},
                ],
            )

        ai_text = completion.choices[0].message.content.strip()
        logger.info(f"🦁 Mufasa says: {ai_text}")

        # --- 2️⃣ Generate voice (optional) ---
        audio_url = None
        if request.voice and OPENVOICE_API_URL:
            try:
                voice_response = requests.post(
                    f"{OPENVOICE_API_URL}/speak",
                    json={"text": ai_text, "voice": "african_male_deep"},
                    timeout=30,
                )

                if voice_response.status_code == 200:
                    os.makedirs("app/static/audio", exist_ok=True)
                    audio_filename = f"{uuid.uuid4()}.mp3"
                    audio_path = f"app/static/audio/{audio_filename}"

                    with open(audio_path, "wb") as f:
                        f.write(voice_response.content)

                    audio_url = f"{BASE_URL}/static/audio/{audio_filename}"
                    logger.info(f"🎵 Voice generated successfully: {audio_url}")
                else:
                    logger.warning(f"⚠️ OpenVoice API error: {voice_response.status_code} - {voice_response.text}")

            except Exception as voice_error:
                logger.error(f"🎤 Voice synthesis failed: {voice_error}")

        # --- 3️⃣ Return standard response ---
        return {
            "reply": ai_text,
            "audio_url": audio_url,
            "source": "MufasaKnowledgeBank",
        }

    except Exception as e:
        logger.error(f"❌ Chat API error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {e}")


# --------------------------
# 🩺 Health Check
# --------------------------
@router.get("/ping")
def ping():
    return {"ok": True, "message": "🦁 Mufasa Chat API is alive and roaring!"}
