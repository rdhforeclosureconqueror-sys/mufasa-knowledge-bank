from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from openai import OpenAI
import requests
import tempfile
import os
import uuid
from pathlib import Path
from app.config import settings

router = APIRouter()

# ==========================================================
# ⚙️ CONFIGURATION
# ==========================================================
STATIC_AUDIO_DIR = Path("app/static/audio")
STATIC_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = settings.OPENAI_API_KEY
AIVOICE_BASE_URL = settings.AIVOICE_API or "https://aivoice-wmrv.onrender.com"
AIVOICE_API_KEY = os.getenv("AIVOICE_API_KEY", "")
BASE_URL = settings.BASE_URL or "https://mufasa-knowledge-bank.onrender.com"

client = OpenAI(api_key=OPENAI_API_KEY)
MUFASA_MODEL = "gpt-4o-mini"

# ==========================================================
# 🧩 HELPERS
# ==========================================================
def aivoice_headers() -> dict:
    """Attach security header for aiVoice API calls."""
    return {"X-AIVOICE-KEY": AIVOICE_API_KEY} if AIVOICE_API_KEY else {}

def generate_audio_filename(ext="mp3") -> Path:
    return STATIC_AUDIO_DIR / f"{uuid.uuid4()}.{ext}"

def save_audio_file(audio_bytes, ext="mp3") -> str:
    """Save binary audio and return public URL."""
    filename = generate_audio_filename(ext)
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    return f"{BASE_URL}/static/audio/{filename.name}"

def openai_response(prompt: str) -> str:
    """Generate Mufasa’s text wisdom via GPT."""
    try:
        completion = client.chat.completions.create(
            model=MUFASA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the Pan-African philosopher and historian. "
                        "Speak with grace, depth, and authority rooted in African history, "
                        "wisdom, and liberation movements."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("❌ OpenAI error:", e)
        raise HTTPException(status_code=500, detail="Mufasa could not respond.")


# ==========================================================
# 💬 1️⃣ TEXT CHAT → GPT → (Optional TTS)
# ==========================================================
@router.post("/message")
async def generate_openai_response(payload: dict):
    """
    Generate Mufasa text reply and (optionally) audio reply via aiVoice.
    """
    message = payload.get("message", "").strip()
    make_voice = payload.get("voice", False)
    voice_model = payload.get("voice_model", "alloy")

    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")

    ai_text = openai_response(message)
    audio_url = None

    # 🎙️ Optional voice synthesis
    if make_voice:
        try:
            tts_response = requests.post(
                f"{AIVOICE_BASE_URL}/tts",
                json={"text": ai_text, "format": "mp3", "voice": voice_model},
                headers=aivoice_headers(),
                timeout=45,
            )
            if tts_response.status_code == 200:
                audio_url = save_audio_file(tts_response.content)
            else:
                print("⚠️ aiVoice TTS failed:", tts_response.text)
        except Exception as e:
            print("🎤 TTS generation failed:", e)

    return {
        "reply": ai_text,
        "audio_url": audio_url,
        "voice": voice_model,
        "source": "MufasaKnowledgeBank",
    }


# ==========================================================
# 🔊 2️⃣ TEXT → SPEECH (Standalone TTS)
# ==========================================================
@router.post("/tts")
async def text_to_speech(payload: dict):
    """
    Convert text into speech only (frontend 'Play Voice' button).
    """
    text = payload.get("text", "").strip()
    voice = payload.get("voice_model", "alloy")

    if not text:
        raise HTTPException(status_code=400, detail="No text provided for TTS.")

    try:
        tts_response = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json={"text": text, "format": "mp3", "voice": voice},
            headers=aivoice_headers(),
            timeout=45,
        )

        if tts_response.status_code == 200:
            audio_url = save_audio_file(tts_response.content)
            return {"audio_url": audio_url, "voice": voice}
        else:
            print("TTS error:", tts_response.text)
            raise HTTPException(status_code=500, detail="TTS failed to generate.")
    except Exception as e:
        print("❌ TTS Exception:", e)
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")


# ==========================================================
# 🎙️ 3️⃣ VOICE INPUT → TRANSCRIBE → GPT → TTS
# ==========================================================
@router.post("/voice")
async def handle_voice_input(file: UploadFile = File(...)):
    """
    Accept voice input, transcribe via Whisper, reply with GPT,
    and return text + voice audio.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Step 1️⃣ Transcribe
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )

        user_text = transcript.text.strip()
        print(f"🎤 Transcribed: {user_text}")

        # Step 2️⃣ GPT Reply
        ai_text = openai_response(user_text)

        # Step 3️⃣ Generate TTS for Reply
        tts_response = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json={"text": ai_text, "format": "mp3", "voice": "alloy"},
            headers=aivoice_headers(),
            timeout=60,
        )

        audio_url = save_audio_file(tts_response.content) if tts_response.status_code == 200 else None
        os.remove(tmp_path)

        return {
            "transcript": user_text,
            "reply": ai_text,
            "audio_url": audio_url,
            "source": "MufasaVoice",
        }

    except Exception as e:
        print("❌ Voice chat error:", e)
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {e}")


# ==========================================================
# 🩺 4️⃣ HEALTH CHECK
# ==========================================================
@router.get("/ping")
async def ping():
    return {"ok": True, "message": "Mufasa Chat API is alive and roaring 🦁"}
