# app/config.py
import os
from dotenv import load_dotenv

# Load .env file (for local development)
load_dotenv()

class Settings:
    # === OpenAI ===
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # === aiVoice API ===
    AIVOICE_BASE_URL: str = os.getenv("AIVOICE_BASE_URL", "https://aivoice-wmrv.onrender.com")
    AIVOICE_API_KEY: str = os.getenv("AIVOICE_API_KEY", "")

    # === App Metadata ===
    BASE_URL: str = os.getenv("BASE_URL", "https://mufasa-knowledge-bank.onrender.com")

settings = Settings()
