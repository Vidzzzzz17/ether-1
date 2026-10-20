import os, tempfile
import httpx
from fastapi import HTTPException, UploadFile
from ..config import get_settings

async def transcribe(upload: UploadFile) -> str:
    settings=get_settings(); data=await upload.read(settings.max_upload_mb*1024*1024+1)
    if len(data)>settings.max_upload_mb*1024*1024: raise HTTPException(status_code=413,detail="Audio file is too large.")
    if settings.whisper_api_url:
        headers={"Authorization":f"Bearer {settings.whisper_api_key}"} if settings.whisper_api_key else {}
        async with httpx.AsyncClient(timeout=120) as client:
            result=await client.post(settings.whisper_api_url,headers=headers,files={"file":(upload.filename or "audio.webm",data,upload.content_type or "audio/webm")},data={"model":"whisper-1"});result.raise_for_status()
        return str(result.json().get("text",""))
    if settings.whisper_model:
        try:
            from faster_whisper import WhisperModel
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(upload.filename or "audio.wav")[1] or ".wav") as temp:
                temp.write(data);temp.flush();model=WhisperModel(settings.whisper_model,device="cpu",compute_type="int8");segments,_=model.transcribe(temp.name)
                return " ".join(segment.text.strip() for segment in segments)
        except ImportError as exc: raise HTTPException(status_code=503,detail="Install the API audio extra to use local Whisper.") from exc
    raise HTTPException(status_code=503,detail="Configure WHISPER_API_URL or WHISPER_MODEL for audio transcription.")

async def synthesize(text: str) -> str | None:
    settings=get_settings()
    if not settings.tts_api_url:return None
    headers={"Authorization":f"Bearer {settings.tts_api_key}"} if settings.tts_api_key else {}
    async with httpx.AsyncClient(timeout=120) as client:
        result=await client.post(settings.tts_api_url,headers=headers,json={"input":text,"text":text});result.raise_for_status()
    return result.json().get("url")

