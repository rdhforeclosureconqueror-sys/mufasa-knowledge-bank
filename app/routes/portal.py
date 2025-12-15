from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.openai_client import generate_portal_response
import os

router = APIRouter()

PORTALS_DIR = os.path.join(os.path.dirname(__file__), "..", "portals")

class PortalRequest(BaseModel):
    portal_id: str
    resume_code: str | None = None
    question: str | None = None

@router.get("/list")
async def list_portals():
    return [f.replace(".txt", "") for f in os.listdir(PORTALS_DIR)]

@router.post("/start")
async def start_portal(req: PortalRequest):
    try:
        response = await generate_portal_response(req.portal_id, None, None)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/continue")
async def continue_portal(req: PortalRequest):
    try:
        response = await generate_portal_response(req.portal_id, req.resume_code, req.question)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
