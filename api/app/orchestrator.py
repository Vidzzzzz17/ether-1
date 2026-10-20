import uuid
from fastapi import HTTPException, UploadFile
from .schemas import Artifact, ChatResponse, Intent
from .handlers.text import generate_text
from .handlers.speech import transcribe, synthesize
from .handlers.image import generate_image

def detect_intent(message: str, requested: str | None, upload: UploadFile | None) -> Intent:
    if upload and (upload.content_type or "").startswith("audio/"): return "audio"
    if requested in ("image","audio"): return requested  # type: ignore[return-value]
    if any(word in message.lower() for word in ("generate an image","create an image","draw ","make an image")): return "image"
    return "text"

async def handle_chat(message: str, intent: Intent, history: list[dict], upload: UploadFile | None, model: str | None = None) -> ChatResponse:
    image_data=None
    if upload and (upload.content_type or "").startswith("image/"):
        from .config import get_settings
        settings=get_settings(); data=await upload.read(settings.max_upload_mb*1024*1024+1)
        if len(data)>settings.max_upload_mb*1024*1024: raise HTTPException(status_code=413,detail="Image file is too large.")
        image_data=(data,upload.content_type or "image/png")
    if upload and intent=="audio": message=(message+"\n\nTranscription: "+await transcribe(upload)).strip()
    if intent=="image": return ChatResponse(reply="Here is the image I generated.",artifacts=[await generate_image(message)],intent=intent)
    reply,artifacts=await generate_text(message,history,image_data,model)
    if intent=="audio":
        audio_url=await synthesize(reply)
        if audio_url:artifacts.append(Artifact(id=str(uuid.uuid4()),type="audio",title="Spoken response",url=audio_url))
    return ChatResponse(reply=reply,artifacts=artifacts,intent=intent)

