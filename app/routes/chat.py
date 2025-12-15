from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import requests
import os
import uuid
import logging

router = APIRouter()

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENVOICE_API_URL = os.getenv("OPENVOICE_API_URL")

openai.api_key = OPENAI_API_KEY

# --- Logging setup ---
logger = logging.getLogger("mufasa-chat")
logger.setLevel(logging.INFO)

# --- Request Schema ---
class ChatRequest(BaseModel):
    message: str
    user_id: str = "guest"
    voice: bool = True


# --- POST /chat/message ---
@router.post("/message")
async def generate_openai_response(request: ChatRequest):
    """
    Main Mufasa chat endpoint.
    Receives user text, returns AI response (and optional audio URL).
    """
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Empty message not allowed.")

        logger.info(f"🗣 Incoming message: {request.message}")

        # --- 1️⃣ Get GPT-4.1 response ---
        completion = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the Pan-African AI historian and philosopher. "
                        "You speak with wisdom, confidence, and deep knowledge of African history, "
                        "heritage, and liberation movements. Always respond in a tone that inspires pride, "
                        "education, and empowerment."
                    ),
                },
                {"role": "user", "content": request.message},
            ],
            temperature=0.7,
        )

        ai_text = completion.choices[0].message.content.strip()
        logger.info(f"🦁 Mufasa says: {ai_text}")

        # --- 2️⃣ Optional: Send to OpenVoice for speech synthesis ---
        audio_url = None
        if request.voice and OPENVOICE_API_URL:
            try:
                voice_response = requests.post(
                    f"{OPENVOICE_API_URL}/speak",
                    json={"text": ai_text, "voice": "african_male_deep"},
                    timeout=30,
                )
                if voice_response.status_code == 200:
                    audio_filename = f"{uuid.uuid4()}.mp3"
                    audio_path = f"app/static/audio/{audio_filename}"

                    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                    with open(audio_path, "wb") as f:
                        f.write(voice_response.content)

                    # URL that frontend can play from Render
                    audio_url = f"https://mufasa-knowledge-bank.onrender.com/static/audio/{audio_filename}"
                    logger.info(f"🎵 Voice generated: {audio_url}")
                else:
                    logger.warning(f"⚠️ OpenVoice failed: {voice_response.status_code}")

            except Exception as voice_error:
                logger.error(f"🎤 Voice synthesis error: {voice_error}")

        # --- 3️⃣ Return JSON matching frontend expectation ---
        return {"reply": ai_text, "audio_url": audio_url, "source": "MufasaKnowledgeBank"}

    except Exception as e:
        logger.error(f"❌ Chat API error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {e}")


# --- Health check route ---
@router.get("/ping")
def ping():
    return {"ok": True, "message": "Mufasa Chat API is alive and roaring 🦁"}
