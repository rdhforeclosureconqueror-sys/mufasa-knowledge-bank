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

MUFASA_MODEL = "gpt-4o-mini"  # or your deployed OpenAI model
AIVOICE_BASE_URL = settings.AIVOICE_API or "https://aivoice-wmrv.onrender.com"

# === Helpers ===

def generate_audio_filename(ext="mp3"):
    return STATIC_AUDIO_DIR / f"{uuid.uuid4()}.{ext}"

def save_audio_file(audio_bytes, ext="mp3"):
    filename = generate_audio_filename(ext)
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    return f"/static/audio/{filename.name}"

def openai_response(prompt: str) -> str:
    """Generate AI text from Mufasa brain"""
    try:
        completion = openai.ChatCompletion.create(
            model=MUFASA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mufasa, the ancient voice of Pan-African wisdom. "
                        "Speak with depth, historical reverence, and dignity. "
                        "Every answer should inspire unity, cultural pride, and learning."
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


# === Routes ===

@router.post("/message")
async def generate_openai_response(payload: dict):
    """
    Generate Mufasa text reply.
    Optionally generate a voice response if voice=True.
    """
    message = payload.get("message", "")
    make_voice = payload.get("voice", False)
    voice_model = payload.get("voice_model", "alloy")

    if not message:
        raise HTTPException(status_code=400, detail="No message provided.")

    ai_text = openai_response(message)
    audio_url = None

    if make_voice:
        try:
            tts_response = requests.post(
                f"{AIVOICE_BASE_URL}/tts",
                json={"text": ai_text, "format": "mp3", "voice": voice_model},
                timeout=60,
            )
            if tts_response.status_code == 200:
                audio_url = save_audio_file(tts_response.content)
            else:
                print("TTS error:", tts_response.text)
        except Exception as e:
            print("TTS generation failed:", e)

    return {
        "reply": ai_text,
        "audio_url": audio_url,
        "voice": voice_model,
        "source": "MufasaKnowledgeBank",
    }


@router.post("/tts")
async def text_to_speech(payload: dict):
    """
    Convert already-generated text into speech only.
    Used when user clicks 'Play Voice' button.
    """
    text = payload.get("text", "").strip()
    voice = payload.get("voice_model", "alloy")

    if not text:
        raise HTTPException(status_code=400, detail="No text provided for TTS.")

    try:
        tts_response = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json={"text": text, "format": "mp3", "voice": voice},
            timeout=45,
        )
        if tts_response.status_code == 200:
            audio_url = save_audio_file(tts_response.content)
            return {"audio_url": audio_url, "voice": voice}
        else:
            raise HTTPException(status_code=500, detail="TTS failed to generate.")
    except Exception as e:
        print("TTS Error:", e)
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")


@router.post("/voice")
async def handle_voice_input(file: UploadFile = File(...)):
    """
    Accept voice input (recorded by user), transcribe to text,
    send to GPT, and respond with text + voice.
    """
    try:
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Step 1: Transcribe
        with open(tmp_path, "rb") as audio_file:
            transcription = openai.Audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
            )
        user_text = transcription.text.strip()

        # Step 2: Get Mufasa reply
        ai_text = openai_response(user_text)

        # Step 3: Generate TTS for reply
        tts_response = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json={"text": ai_text, "format": "mp3", "voice": "alloy"},
            timeout=60,
        )

        if tts_response.status_code == 200:
            audio_url = save_audio_file(tts_response.content)
        else:
            audio_url = None

        os.remove(tmp_path)
        return {
            "user_text": user_text,
            "reply": ai_text,
            "audio_url": audio_url,
            "source": "MufasaVoice",
        }

    except Exception as e:
        print("Voice chat error:", e)
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {e}")
