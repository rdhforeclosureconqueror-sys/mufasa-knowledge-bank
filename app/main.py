from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, portal
import os

app = FastAPI(
    title="Mufasa Knowledge Bank API",
    description="Backend API for Prince of Pan-Africa — integrated with OpenAI + OpenVoice.",
    version="1.0.0"
)

# ----------------------------------------------------------------
# ✅ CORS CONFIGURATION
# Allow frontend (Render static site) to access backend API
# ----------------------------------------------------------------
origins = [
    "http://localhost:5173",  # local dev
    "https://prince-of-pan-africa.onrender.com",  # deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------
# ✅ ROUTERS
# ----------------------------------------------------------------
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(portal.router, prefix="/portal", tags=["Portals"])

# ----------------------------------------------------------------
# ✅ HEALTH + ROOT ENDPOINTS
# ----------------------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Mufasa Knowledge Bank is live. Visit /docs for API routes.",
        "frontend_url": "https://prince-of-pan-africa.onrender.com"
    }

@app.get("/health")
def health():
    return {"ok": True, "service": "Mufasa Knowledge Bank"}

# ----------------------------------------------------------------
# ✅ OPENAI / OPENVOICE ENVIRONMENT SETUP CHECK
# ----------------------------------------------------------------
@app.get("/env-check")
def env_check():
    openai_key = os.getenv("OPENAI_API_KEY")
    openvoice_url = os.getenv("OPENVOICE_API_URL")

    return {
        "openai_configured": bool(openai_key),
        "openvoice_configured": bool(openvoice_url),
        "note": "Both should be True for full functionality."
    }
