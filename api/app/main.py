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

@app.get("/api/health")
async def health(): return {"status":"ok"}

@app.post("/api/v1/chat",response_model=ChatResponse)
async def chat(authorization: str|None=Header(default=None),message: str=Form(default=""),intent: str|None=Form(default=None),history: str=Form(default="[]"),file: UploadFile|None=File(default=None)):
    await require_user(authorization)
    if not message.strip() and not file: raise HTTPException(status_code=422,detail="Add a message or attach an audio file.")
    try:
        parsed_history=json.loads(history)
        if not isinstance(parsed_history,list):raise ValueError
    except ValueError:raise HTTPException(status_code=422,detail="History must be a JSON array.")
    routed=detect_intent(message,intent,file)
    try:return await handle_chat(message.strip(),routed,parsed_history,file)
    except HTTPException:raise
    except Exception as exc:raise HTTPException(status_code=502,detail=str(exc)) from exc

