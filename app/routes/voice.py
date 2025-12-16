from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import requests
import os
import logging

router = APIRouter()
AIVOICE_BASE_URL = os.getenv("AIVOICE_BASE_URL", "https://aivoice-wmrv.onrender.com")
logger = logging.getLogger("mufasa-voice")
logger.setLevel(logging.INFO)


class TTSRequest(BaseModel):
    text: str
    format: str | None = "mp3"
    voice: str | None = "alloy"


@router.post("/tts")
async def proxy_tts(req: TTSRequest):
    """Proxy text → speech via aiVoice"""
    try:
        res = requests.post(
            f"{AIVOICE_BASE_URL}/tts",
            json=req.dict(),
            timeout=60,
        )

        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.text)

        media_type = res.headers.get("content-type", "audio/mpeg")
        return StreamingResponse(iter([res.content]), media_type=media_type)
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")


@router.post("/stt")
async def proxy_stt(file: UploadFile = File(...)):
    """Proxy speech → text via aiVoice"""
    try:
        files = {"file": (file.filename, await file.read(), file.content_type)}
        res = requests.post(f"{AIVOICE_BASE_URL}/stt", files=files, timeout=90)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.text)
        return JSONResponse(res.json())
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")
