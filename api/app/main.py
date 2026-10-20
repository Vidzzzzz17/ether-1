import json
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
import httpx
from fastapi.middleware.cors import CORSMiddleware
from .auth import require_user
from .config import get_settings
from .orchestrator import detect_intent, handle_chat
from .schemas import ChatResponse

settings=get_settings();app=FastAPI(title="Ether 1 API",version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=True,allow_methods=["GET","POST","OPTIONS"],allow_headers=["Authorization","Content-Type"])

@app.get("/api/models")
async def models():
    catalog = {
        "qwen2.5:7b": {"name": "Qwen2.5 7B", "capabilities": ["chat"]},
        "qwen2.5-coder:7b": {"name": "Qwen2.5 Coder 7B", "capabilities": ["chat", "code"]},
        "qwen2.5vl:7b": {"name": "Qwen2.5 VL 7B", "capabilities": ["chat", "image-understanding"]},
    }
    choices = [{"id": model, **catalog.get(model, {"name": model, "capabilities": ["chat"]})} for model in settings.available_llm_models]
    installed = None
    try:
        base = settings.llm_base_url.removesuffix("/v1").rstrip("/")
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{base}/api/tags")
            response.raise_for_status()
            installed = {item.get("name") for item in response.json().get("models", [])}
        for item in choices:
            item["installed"] = item["id"] in installed
    except (httpx.HTTPError, ValueError):
        for item in choices:
            item["installed"] = None
    return {"default": settings.llm_model, "models": choices}

@app.get("/api/health")
async def health(): return {"status":"ok"}

@app.post("/api/v1/chat",response_model=ChatResponse)
async def chat(authorization: str|None=Header(default=None),message: str=Form(default=""),intent: str|None=Form(default=None),history: str=Form(default="[]"),model: str|None=Form(default=None),file: UploadFile|None=File(default=None)):
    await require_user(authorization)
    if model and model not in settings.available_llm_models: raise HTTPException(status_code=422,detail="Choose a model from the configured local model list.")
    if not message.strip() and not file: raise HTTPException(status_code=422,detail="Add a message or attach an audio file.")
    try:
        parsed_history=json.loads(history)
        if not isinstance(parsed_history,list):raise ValueError
    except ValueError:raise HTTPException(status_code=422,detail="History must be a JSON array.")
    routed=detect_intent(message,intent,file)
    try:return await handle_chat(message.strip(),routed,parsed_history,file,model)
    except HTTPException:raise
    except Exception as exc:raise HTTPException(status_code=502,detail=str(exc)) from exc

