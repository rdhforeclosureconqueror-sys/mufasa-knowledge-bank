from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from openai import OpenAI
import requests
import os
import uuid
import logging

router = APIRouter()

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIVOICE_BASE_URL = os.getenv("AIVOICE_BASE_URL", "https://aivoice-wmrv.onrender.com")
BASE_URL = os.getenv("BASE_URL", "https://mufasa-knowledge-bank.onrender.com")

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Logging setup ---
logger = logging.getLogger("mufasa-chat")
logger.setLevel(logging.INFO)

# --- Request schema ---
class ChatRequest(BaseModel):
    message: str
    user_id: str = "guest"
    voice: bool = True


# ==========================================================
# 🧠 1️⃣ Text Chat (with optional Voice)
# ==========================================================
@router.post("/message")
async def generate_openai_response(request: ChatRequest):
    """
    Mufasa chat endpoint — handles text conversation and optionally generates voice via aiVoice.
    """
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Empty message not allowed.")

        logger.info(f"🗣 Incoming message: {request.message}")

        # --- 1️⃣ Generate GPT response ---
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the Pan-African AI historian and philosopher. "
                        "Speak with wisdom, confidence, and deep knowledge of African history, "
                        "heritage, and liberation movements. You inspire pride and unity."
                    ),
                },
                {"role": "user", "content": request.message},
            ],
            temperature=0.7,
        )

        ai_text = completion.choices[0].message.content.strip()
        logger.info(f"🦁 Mufasa replies: {ai_text}")

        # --- 2️⃣ Send reply text to aiVoice for speech synthesis ---
        audio_url = None
        if request.voice:
            try:
                tts_response = requests.post(
                    f"{AIVOICE_BASE_URL}/tts",
                    json={"text": ai_text, "format": "mp3"},
                    timeout=60,
                )

                if tts_response.status_code == 200:
                    # Save locally in static/audio
                    audio_filename = f"{uuid.uuid4()}.mp3"
                    audio_path = f"app/static/audio/{audio_filename}"

                    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                    with open(audio_path, "wb") as f:
                        f.write(tts_response.content)

                    audio_url = f"{BASE_URL}/static/audio/{audio_filename}"
                    logger.info(f"🎵 Voice generated at: {audio_url}")
                else:
                    logger.warning(f"⚠️ aiVoice TTS failed ({tts_response.status_code}): {tts_response.text}")

            except Exception as voice_error:
                logger.error(f"🎤 Voice synthesis error: {voice_error}")

        # --- 3️⃣ Return combined response ---
        return {"reply": ai_text, "audio_url": audio_url, "source": "MufasaKnowledgeBank"}

    except Exception as e:
        logger.error(f"❌ Chat API error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {e}")


# ==========================================================
# 🎙️ 2️⃣ Voice Chat (Speech → Text → Brain → Speech)
# ==========================================================
@router.post("/voice")
async def chat_with_voice(file: UploadFile = File(...)):
    """
    Full voice conversation pipeline:
    1. Transcribe speech via aiVoice /stt
    2. Get GPT reply (Mufasa brain)
    3. Convert reply to speech via aiVoice /tts
    """
    try:
        # --- Step 1: Transcribe the uploaded audio ---
        stt_response = requests.post(
            f"{AIVOICE_BASE_URL}/stt",
            files={"file": (file.filename, await file.read(), file.content_type)},
            timeout=90,
        )
        stt_response.raise_for_status()

        transcript = stt_response.json().get("text", "").strip()
        if not transcript:
            raise Exception("Empty transcript returned from aiVoice STT")

        logger.info(f"🗣 Transcribed: {transcript}")

        # --- Step 2: Generate Mufasa's reply via GPT ---
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the Pan-African AI historian and philosopher. "
                        "Speak with power, warmth, and knowledge of African legacy and unity."
                    ),
                },
                {"role": "user", "content": transcript},
            ],
            temperature=0.7,
        )

        reply_text = completion.choices[0].message.content.strip()
        logger.info(f"🦁 Mufasa replies (voice): {reply_text}")

        # --- Step 3: Convert reply text to audio ---
        tts_response = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json={"text": reply_text, "format": "mp3"},
            timeout=90,
        )
        tts_response.raise_for_status()

        # --- Step 4: Save MP3 locally ---
        filename = f"{uuid.uuid4()}.mp3"
        audio_path = f"app/static/audio/{filename}"
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, "wb") as f:
            f.write(tts_response.content)

        audio_url = f"{BASE_URL}/static/audio/{filename}"

        logger.info(f"🎧 Voice chat complete → {audio_url}")

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
# 🩺 3️⃣ Health Check
# ==========================================================
@router.get("/ping")
def ping():
    return {"ok": True, "message": "Mufasa Chat API is alive and roaring 🦁"}
