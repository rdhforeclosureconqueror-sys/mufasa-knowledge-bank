from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import chat, portal, voice
import os

# 1️⃣ Initialize FastAPI app
app = FastAPI(
    title="Mufasa Knowledge Bank API",
    description=(
        "Backend intelligence for the Prince of Pan-Africa platform — "
        "integrating text, voice, and image AI features aligned with the Maat principles."
    ),
    version="1.0.0",
)

# 2️⃣ Configure CORS (Cross-Origin Resource Sharing)
# You can later restrict this to your frontend URL via ALLOWED_ORIGINS.
default_origins = [
    "https://prince-of-pan-africa.onrender.com",
    "https://mufasa-knowledge-bank.onrender.com",
]
raw_allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = (
    [origin.strip() for origin in raw_allowed_origins.split(",") if origin.strip()]
    if raw_allowed_origins
    else default_origins
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3️⃣ Ensure static directory exists
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# 4️⃣ Mount static folder for images, audio, and other assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 5️⃣ Include routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(portal.router, prefix="/portal", tags=["Portals"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])  # 👈 new addition

# 6️⃣ Root endpoint (for quick status check)
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Mufasa Knowledge Bank",
        "frontend": "Prince of Pan-Africa",
        "message": "Mufasa Knowledge Bank is live. Visit /docs for API routes.",
    }

# 7️⃣ Health check endpoint
@app.get("/health")
def health():
    return {"ok": True, "service": "Mufasa Knowledge Bank", "environment": "production"}

# 8️⃣ Info endpoint (for debugging or admin dashboard)
@app.get("/info")
def info():
    return {
        "app_name": app.title,
        "version": app.version,
        "static_path": "/static",
        "routes": [route.path for route in app.routes],
    }

# 9️⃣ Startup event log
@app.on_event("startup")
async def startup_event():
    print("🔥 Mufasa Knowledge Bank is awake and ready to serve the Pride!")
