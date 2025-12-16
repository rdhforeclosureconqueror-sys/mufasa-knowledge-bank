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
AIVOICE_URL = os.getenv("OPENVOICE_API_URL")  # Now points to aiVoice
openai.api_key = OPENAI_API_KEY

logger = logging.getLogger("mufasa-chat")
logger.setLevel(logging.INFO)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "guest"
    voice: bool = True

@router.post("/message")
async def generate_openai_response(request: ChatRequest):
    """
    Mufasa chat endpoint (text + optional voice)
    """
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Empty message not allowed.")

        logger.info(f"🗣 Incoming message: {request.message}")

        # --- 1️⃣ Get GPT response ---
        completion = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": (
                    "You are Mufasa, the Pan-African AI historian and philosopher. "
                    "You speak with wisdom, confidence, and deep knowledge of African history, "
                    "heritage, and liberation movements."
                )},
                {"role": "user", "content": request.message},
            ],
            temperature=0.7,
        )

        ai_text = completion.choices[0].message.content.strip()
        logger.info(f"🦁 Mufasa says: {ai_text}")

        # --- 2️⃣ Send text to aiVoice for TTS ---
        audio_url = None
        if request.voice and AIVOICE_URL:
            try:
                tts_res = requests.post(
                    f"{AIVOICE_URL}/speak",
                    json={"text": ai_text, "format": "mp3"},
                    timeout=60,
                )

                if tts_res.status_code == 200:
                    # Save the MP3 file
                    audio_filename = f"{uuid.uuid4()}.mp3"
                    audio_path = f"app/static/audio/{audio_filename}"

                    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                    with open(audio_path, "wb") as f:
                        f.write(tts_res.content)

                    # Build the public audio URL
                    base_url = os.getenv("BASE_URL", "https://mufasa-knowledge-bank.onrender.com")
                    audio_url = f"{base_url}/static/audio/{audio_filename}"
                    logger.info(f"🎵 Voice generated: {audio_url}")

                else:
                    logger.warning(f"⚠️ aiVoice failed ({tts_res.status_code}): {tts_res.text}")

            except Exception as voice_error:
                logger.error(f"🎤 Voice synthesis error: {voice_error}")

        # --- 3️⃣ Return text + voice URL ---
        return {"reply": ai_text, "audio_url": audio_url, "source": "MufasaKnowledgeBank"}

    except Exception as e:
        logger.error(f"❌ Chat API error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {e}")
