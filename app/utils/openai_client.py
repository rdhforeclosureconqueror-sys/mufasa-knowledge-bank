import os
import openai
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENVOICE_URL = os.getenv("OPENVOICE_URL", "https://ffmpeg-9xhs.onrender.com")

client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_portal_text(portal_id: str) -> str:
    base_path = os.path.join(os.path.dirname(__file__), "..", "portals")
    path = os.path.join(base_path, f"{portal_id}.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Portal {portal_id} not found.")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

async def generate_openai_response(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Mufasa, an unpolarized historian assistant guided by African and world wisdom systems. Always provide sources, tiers, and verify steps."},
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content

async def generate_portal_response(portal_id: str, resume_code: str | None, question: str | None):
    portal_text = load_portal_text(portal_id)
    context_prompt = f"{portal_text}\n\nRESUME_CODE={resume_code or 'DAY1'}\nQUESTION={question or 'Start'}"
    response = await generate_openai_response(context_prompt)
    return {"portal": portal_id, "response": response}
