from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import requests
import os
import uuid

router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENVOICE_API_URL = os.getenv("OPENVOICE_API_URL")

openai.api_key = OPENAI_API_KEY


class ChatRequest(BaseModel):
    message: str
    user_id: str = "guest"
    voice: bool = True


@router.post("/message")
async def generate_openai_response(request: ChatRequest):
    try:
        # --- 1️⃣ Get OpenAI response ---
        completion = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are Mufasa, the Pan-African AI historian and philosopher."},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7
        )

        ai_text = completion.choices[0].message.content.strip()

        # --- 2️⃣ Optional: Send to OpenVoice for speech synthesis ---
        audio_url = None
        if request.voice and OPENVOICE_API_URL:
            response = requests.post(
                f"{OPENVOICE_API_URL}/speak",
                json={"text": ai_text, "voice": "african_male_deep"},
                timeout=30
            )
            if response.status_code == 200:
                audio_filename = f"{uuid.uuid4()}.mp3"
                audio_path = f"static/audio/{audio_filename}"
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                audio_url = f"https://mufasa-knowledge-bank.onrender.com/{audio_path}"

        # --- 3️⃣ Return response to frontend ---
        return {"text": ai_text, "audio_url": audio_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
