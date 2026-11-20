import os
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import httpx
import automation

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jarvis")

app = FastAPI(
    title="JARVIS AI — Personal Voice Assistant",
    description="Local AI Voice Assistant powered by Ollama and FastAPI with Windows Automation",
    version="1.1.0"
)

# Configuration from environment or defaults
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:latest")

JARVIS_SYSTEM_PROMPT = """You are JARVIS (Just A Rather Very Intelligent System), a sophisticated, witty, and highly capable personal AI assistant inspired by Tony Stark's JARVIS.
You communicate naturally, intelligently, and with refined polite undertones.
Because your answers are spoken aloud through browser speech synthesis, follow these guidelines:
1. Speak concisely, clearly, and conversationally.
2. Avoid excessive markdown symbols, asterisks, bulleted walls of text, or emojis unless explicitly requested.
3. Keep spoken replies punchy and engaging.
4. Address the user respectfully (e.g. 'sir' or politely) when appropriate.
5. If providing code, give a brief conversational overview first.

SYSTEM AUTOMATION INSTRUCTIONS:
You have control over the user's Windows operating system. If the user asks you to perform an action, append the appropriate action tag:
- Open website: [ACTION: OPEN_URL url="https://..."]
- Search YouTube: [ACTION: YOUTUBE_SEARCH query="..."]
- Search Google: [ACTION: GOOGLE_SEARCH query="..."]
- Open standard folder: [ACTION: OPEN_FOLDER path="downloads/desktop/documents/pictures/videos/music"]
- Open application: [ACTION: OPEN_APP name="notepad/calculator/code/chrome/cmd/settings/taskmgr"]
Always accompany action tags with a brief polite confirmation (e.g. "Opening YouTube for you now, sir. [ACTION: OPEN_URL url=\"https://www.youtube.com\"]")."""

# Pydantic Schemas
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []
    model: Optional[str] = None
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    status: str
    action: Optional[str] = None

# API Endpoints
@app.get("/api/status")
async def get_status():
    """Check connectivity with the local Ollama instance."""
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "online": True,
                    "ollama_url": OLLAMA_BASE_URL,
                    "default_model": DEFAULT_MODEL,
                    "available_models": models,
                    "automation": "active",
                    "message": "Ollama and Windows Automation services active."
                }
            return {
                "online": False,
                "ollama_url": OLLAMA_BASE_URL,
                "default_model": DEFAULT_MODEL,
                "error": f"Ollama returned status code {resp.status_code}"
            }
    except Exception as exc:
        logger.warning(f"Failed to connect to Ollama at {OLLAMA_BASE_URL}: {exc}")
        return {
            "online": False,
            "ollama_url": OLLAMA_BASE_URL,
            "default_model": DEFAULT_MODEL,
            "error": "Ollama service unreachable. Ensure Ollama is running on port 11434."
        }

@app.get("/api/models")
async def get_models():
    """Fetch installed Ollama models."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "models": models,
                    "active_default": DEFAULT_MODEL if (DEFAULT_MODEL in models or not models) else models[0]
                }
            raise HTTPException(status_code=resp.status_code, detail="Unable to retrieve models from Ollama")
    except Exception as exc:
        logger.error(f"Error fetching models: {exc}")
        return {"models": [DEFAULT_MODEL], "active_default": DEFAULT_MODEL, "warning": str(exc)}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send user message to automation engine or Ollama."""
    chosen_model = request.model.strip() if request.model else DEFAULT_MODEL
    sys_prompt = request.system_prompt.strip() if request.system_prompt else JARVIS_SYSTEM_PROMPT

    # 1. Fast Path: Direct Windows Automation Command Parser
    auto_result = automation.parse_voice_directive(request.message)
    if auto_result:
        logger.info(f"Direct automation executed: {auto_result.get('action')}")
        return ChatResponse(
            response=auto_result["response"],
            model="system:automation",
            status="success",
            action=auto_result.get("action")
        )

    # 2. General Query Path: Dispatch to Ollama LLM
    messages = [{"role": "system", "content": sys_prompt}]

    if request.history:
        for msg in request.history:
            if msg.role in ("user", "assistant"):
                messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": request.message})

    payload = {
        "model": chosen_model,
        "messages": messages,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            logger.info(f"Dispatching query to Ollama model '{chosen_model}'...")
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload
            )

            if resp.status_code != 200:
                error_detail = resp.text
                logger.error(f"Ollama error ({resp.status_code}): {error_detail}")
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Ollama server error: {error_detail}"
                )

            data = resp.json()
            assistant_message = data.get("message", {}).get("content", "")

            if not assistant_message:
                assistant_message = "I processed your request, sir, but received an empty response."

            # Check and execute any action tags emitted by Ollama
            cleaned_message, action_info = automation.execute_action_tag(assistant_message)
            action_name = action_info.get("type") if action_info else None

            return ChatResponse(
                response=cleaned_message,
                model=chosen_model,
                status="success",
                action=action_name
            )

    except httpx.ConnectError:
        logger.error(f"Could not connect to Ollama at {OLLAMA_BASE_URL}")
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Please make sure Ollama is running (`ollama serve`)."
        )
    except httpx.ReadTimeout:
        logger.error(f"Ollama request timed out after 120 seconds")
        raise HTTPException(
            status_code=504,
            detail="Ollama request timed out. The local model took too long to generate a response."
        )
    except Exception as exc:
        logger.error(f"Unexpected error in /api/chat: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

# Serve static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse(
        {"status": "JARVIS AI backend online", "static_warning": "index.html not found"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
