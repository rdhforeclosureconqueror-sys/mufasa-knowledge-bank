from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.openai_client import generate_portal_response
import openai
import os
import base64
from uuid import uuid4

# Router initialization
router = APIRouter()

# Directories
PORTALS_DIR = os.path.join(os.path.dirname(__file__), "..", "portals")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "images")

# Load API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


# --- 1️⃣ Existing Portal Routes ---

class PortalRequest(BaseModel):
    portal_id: str
    resume_code: str | None = None
    question: str | None = None


@router.get("/list")
async def list_portals():
    """List all available portals in the system"""
    try:
        return [f.replace(".txt", "") for f in os.listdir(PORTALS_DIR)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing portals: {str(e)}")


@router.post("/start")
async def start_portal(req: PortalRequest):
    """Start a new portal learning session"""
    try:
        response = await generate_portal_response(req.portal_id, None, None)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continue")
async def continue_portal(req: PortalRequest):
    """Continue an existing portal session"""
    try:
        response = await generate_portal_response(req.portal_id, req.resume_code, req.question)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 2️⃣ New: AI Image Generator Route ---

class ImageRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"  # Options: 256x256, 512x512, 1024x1024


@router.post("/create_image")
async def create_image(req: ImageRequest):
    """
    Create an AI-generated image based on text prompt.
    Returns a hosted image URL.
    """
    try:
        # Ensure image directory exists
        os.makedirs(IMAGES_DIR, exist_ok=True)

        # Generate image using OpenAI image model
        result = openai.images.generate(
            model="gpt-image-1",
            prompt=req.prompt,
            size=req.size
        )

        # Decode image data
        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)
        image_filename = f"{uuid4()}.png"
        image_path = os.path.join(IMAGES_DIR, image_filename)

        # Save image locally
        with open(image_path, "wb") as f:
            f.write(image_bytes)

        # Build accessible URL for frontend
        image_url = f"https://mufasa-knowledge-bank.onrender.com/static/images/{image_filename}"

        return {"prompt": req.prompt, "image_url": image_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
