from fastapi import FastAPI
from app.routes import chat, portal

app = FastAPI(title="Mufasa Knowledge Bank API")

app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(portal.router, prefix="/portal", tags=["Portals"])

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Mufasa Knowledge Bank is live. Visit /docs for API routes."
    }

@app.get("/health")
def health():
    return {"ok": True}
