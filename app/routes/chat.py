from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.openai_client import generate_openai_response

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/ask")
async def ask_mufasa(req: ChatRequest):
    try:
        response = await generate_openai_response(req.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
