from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import chat, portal

# 1️⃣ Create the FastAPI instance first
app = FastAPI(title="Mufasa Knowledge Bank API")

# 2️⃣ Mount your static directory after app is defined
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3️⃣ Include your routers (chat + portal)
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(portal.router, prefix="/portal", tags=["Portals"])

# 4️⃣ Root endpoint
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Mufasa Knowledge Bank is live. Visit /docs for API routes."
    }

# 5️⃣ Health check
@app.get("/health")
def health():
    return {"ok": True}
