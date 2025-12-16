# app/routes/chat.py
from fastapi import APIRouter, UploadFile, File, HTTPException
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
AIVOICE_BASE_URL = settings.AIVOICE_BASE_URL
AIVOICE_API_KEY = settings.AIVOICE_API_KEY
OPENAI_API_KEY = settings.OPENAI_API_KEY

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY


# === Helpers ===
def aivoice_headers():
    """Return authentication headers for aiVoice"""
    headers = {"Content-Type": "application/json"}
    if AIVOICE_API_KEY:
        headers["X-AIVOICE-KEY"] = AIVOICE_API_KEY
    return headers


def generate_audio_filename(ext="mp3"):
    """Generate unique audio filename"""
    return STATIC_AUDIO_DIR / f"{uuid.uuid4()}.{ext}"


def save_audio_file(audio_bytes, ext="mp3"):
    """Save generated TTS bytes into static/audio"""
    filename = generate_audio_filename(ext)
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    return f"/static/audio/{filename.name}"


def openai_response(prompt: str) -> str:
    """Generate text reply from Mufasa (OpenAI GPT)"""
    try:
        print(f"🦁 Mufasa thinking about: {prompt}")
        completion = openai.ChatCompletion.create(
            model=MUFASA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the ancient voice of Pan-African wisdom. "
                        "Speak with majesty, history, and reverence for Africa’s legacy. "
                        "Inspire unity, truth, and learning with every response."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )
        reply = completion.choices[0].message.content.strip()
        print(f"🦁 Mufasa replied: {reply[:80]}...")  # log first part only
        return reply
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        raise HTTPException(status_code=500, detail="Mufasa failed to think.")


# === ROUTES ===

@router.get("/ping")
async def ping_mufasa():
    """Simple health check"""
    return {"status": "ok", "message": "Mufasa is awake and wise."}


@router.post("/message")
async def generate_openai_response(payload: dict):
    """
    Generate Mufasa text reply.
    Optionally generate a voice response if voice=True.
    """
    message = payload.get("message", "").strip()
    make_voice = payload.get("voice", False)
    voice_model = payload.get("voice_model", "alloy")

    if not message:
        raise HTTPException(status_code=400, detail="No message provided.")

    ai_text = openai_response(message)
    audio_url = None

    if make_voice:
        try:
            print(f"🎤 Sending to aiVoice ({voice_model}) → {AIVOICE_BASE_URL}/tts")
            print(f"🔑 Using header X-AIVOICE-KEY: {AIVOICE_API_KEY[:10]}******")
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
                print(f"❌ aiVoice TTS error {tts_response.status_code}: {tts_response.text}")

        except Exception as e:
            print(f"❌ Voice generation error: {e}")

    return {
        "reply": ai_text,
        "audio_url": audio_url,
        "voice": voice_model,
        "source": "MufasaKnowledgeBank",
    }


@router.post("/tts")
async def text_to_speech(payload: dict):
    """
    Convert text to speech manually (when user clicks 'Play Voice').
    """
    text = payload.get("text", "").strip()
    voice = payload.get("voice_model", "alloy")

    if not text:
        raise HTTPException(status_code=400, detail="No text provided for TTS.")

    try:
        print(f"🎧 Generating TTS for {voice} via {AIVOICE_BASE_URL}/tts")
        tts_response = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json={"text": text, "format": "mp3", "voice": voice},
            headers=aivoice_headers(),
            timeout=45,
        )

        if tts_response.status_code == 200:
            audio_url = save_audio_file(tts_response.content)
            print(f"✅ Saved TTS file: {audio_url}")
            return {"audio_url": audio_url, "voice": voice}
        else:
            print(f"❌ aiVoice returned {tts_response.status_code}: {tts_response.text}")
            raise HTTPException(status_code=500, detail="TTS failed to generate.")

    except Exception as e:
        print(f"❌ TTS Exception: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")


@router.post("/voice")
async def handle_voice_input(file: UploadFile = File(...)):
    """
    Accept user voice input, transcribe → generate reply → convert to TTS.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Step 1: Transcribe
        print("🎙️ Transcribing voice input with OpenAI Whisper model...")
        with open(tmp_path, "rb") as audio_file:
            transcription = openai.Audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
            )
        user_text = transcription.text.strip()
        print(f"🗣️ User said: {user_text}")

        # Step 2: Generate Mufasa reply
        ai_text = openai_response(user_text)

        # Step 3: Generate voice for reply
        print(f"🎧 Generating aiVoice TTS from Mufasa reply → {AIVOICE_BASE_URL}/tts")
        tts_response = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json={"text": ai_text, "format": "mp3", "voice": "alloy"},
            headers=aivoice_headers(),
            timeout=60,
        )

        audio_url = None
        if tts_response.status_code == 200:
            audio_url = save_audio_file(tts_response.content)
            print(f"✅ Voice reply saved: {audio_url}")
        else:
            print(f"❌ aiVoice TTS failed: {tts_response.status_code} {tts_response.text}")

        os.remove(tmp_path)

        return {
            "user_text": user_text,
            "reply": ai_text,
            "audio_url": audio_url,
            "source": "MufasaVoice",
        }

    except Exception as e:
        print(f"❌ Voice chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {e}")
