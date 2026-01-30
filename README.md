# 🦁 Mufasa Knowledge Bank

**Purpose:** Core backend for the Prince of Pan-Africa platform.  
Coordinates OpenAI GPT and OpenVoice APIs for text, speech, and structured portal-based learning.

## Endpoints
| Endpoint | Description |
|-----------|--------------|
| `/chat/ask` | General chat with context |
| `/portal/list` | List all portal codes |
| `/portal/start` | Start a 30-day portal |
| `/portal/continue` | Continue a portal with RESUME_CODE |
| `/health` | Health check |

---

## Environment Variables
- `OPENAI_API_KEY`
- `OPENVOICE_URL` (default: https://ffmpeg-9xhs.onrender.com)
- `ALLOWED_ORIGINS` (comma-separated list of frontend URLs for CORS)
