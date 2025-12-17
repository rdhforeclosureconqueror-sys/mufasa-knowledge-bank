import httpx, os

OPENVOICE_URL = os.getenv("OPENVOICE_URL", "https://aivoice-wmrv.onrender.com")

async def text_to_speech(text: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{OPENVOICE_URL}/tts", json={"text": text})
        return res.json()

async def speech_to_text(audio_url: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{OPENVOICE_URL}/stt", json={"url": audio_url})
        return res.json()
