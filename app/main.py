from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import chat, portal

# 1️⃣ Initialize FastAPI app
app = FastAPI(
    title="Mufasa Knowledge Bank API",
    description="Backend intelligence for the Prince of Pan-Africa platform — integrating text, voice, and image AI features.",
    version="1.0.0",
)

# 2️⃣ Allow cross-origin access (so your frontend on Render can call the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can later tighten this to your Render front-end URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3️⃣ Mount static folder for images, audio, etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

# 4️⃣ Include routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(portal.router, prefix="/portal", tags=["Portals"])

# 5️⃣ Root endpoint (for quick status check)
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Mufasa Knowledge Bank is live. Visit /docs for API routes.",
    }

# 6️⃣ Health check endpoint
@app.get("/health")
def health():
    return {"ok": True, "service": "Mufasa Knowledge Bank"}

# 7️⃣ Startup event log
@app.on_event("startup")
async def startup_event():
    print("🔥 Mufasa Knowledge Bank is awake and ready to serve the Pride!")
