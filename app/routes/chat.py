from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import openai
import requests
import tempfile
import os
import uuid
from pathlib import Path
from app.config import settings

router = APIRouter()

# === Constants ===
STATIC_AUDIO_DIR = Path("app/static/audio")
STATIC_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

MUFASA_MODEL = "gpt-4o-mini"
AIVOICE_BASE_URL = settings.AIVOICE_API or "https://aivoice-wmrv.onrender.com"
AIVOICE_API_KEY = os.getenv("AIVOICE_API_KEY", "")

# === Helpers ===
def aivoice_headers():
    return {"X-AIVOICE-KEY": AIVOICE_API_KEY, "Content-Type": "application/json"}

def generate_audio_filename(ext="mp3"):
    return STATIC_AUDIO_DIR / f"{uuid.uuid4()}.{ext}"

def save_audio_file(audio_bytes, ext="mp3"):
    filename = generate_audio_filename(ext)
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    return f"/static/audio/{filename.name}"

def openai_response(prompt: str) -> str:
    try:
        completion = openai.ChatCompletion.create(
            model=MUFASA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the ancient voice of Pan-African wisdom. "
                        "Speak with depth, pride, and dignity. Inspire unity and learning."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI error:", e)
        raise HTTPException(status_code=500, detail="Mufasa failed to think.")

# === ✅ FIXED ROUTE: /chat/message ===
@router.post("/message")
async def generate_openai_response(payload: dict):
    """
    Generate Mufasa's text reply, and optionally a voice version.
    """
    message = payload.get("message", "").strip()
    make_voice = payload.get("voice", False)
    voice_model = payload.get("voice_model", "alloy")

    if not message:
        raise HTTPException(status_code=400, detail="No message provided.")

    print(f"🦁 Mufasa thinking about: {message}")
    ai_text = openai_response(message)
    audio_url = None

    if make_voice:
        try:
            print(f"🎤 Sending text to aiVoice for {voice_model}")
            tts_response = requests.post(
                f"{AIVOICE_BASE_URL}/tts",
                json={"text": ai_text, "format": "mp3", "voice": voice_model},
                headers=aivoice_headers(),
                timeout=60,
            )

            if tts_response.status_code == 200:
                audio_url = save_audio_file(tts_response.content)
                print(f"✅ Voice generated: {audio_url}")
            else:
                print(f"❌ TTS failed: {tts_response.status_code} {tts_response.text}")

        except Exception as e:
            print("❌ Voice generation error:", e)

    return {
        "reply": ai_text,
        "audio_url": audio_url,
        "voice": voice_model,
        "source": "MufasaKnowledgeBank",
    }
