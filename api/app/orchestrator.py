import uuid

from fastapi import HTTPException, UploadFile

from .config import get_settings
from .handlers.image import generate_image
from .handlers.speech import synthesize, transcribe
from .handlers.text import generate_text
from .router import plan
from .schemas import Artifact, ChatResponse, Intent


def detect_intent(message: str, requested: str | None, upload: UploadFile | None) -> Intent:
    if upload and (upload.content_type or "").startswith("audio/"):
        return "audio"
    if requested in ("image", "audio"):
        return requested  # type: ignore[return-value]
    if any(word in message.lower() for word in ("generate an image", "create an image", "draw ", "make an image")):
        return "image"
    return "text"


async def handle_chat(message: str, intent: Intent, history: list[dict], upload: UploadFile | None) -> ChatResponse:
    settings = get_settings()
    route: list[str] = []
    image_data = None
    audio_upload = upload if upload and (upload.content_type or "").startswith("audio/") else None
    if upload and (upload.content_type or "").startswith("image/"):
        data = await upload.read(settings.max_upload_mb * 1024 * 1024 + 1)
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image file is too large.")
        image_data = (data, upload.content_type or "image/png")
    if audio_upload:
        message = (message + "\n\n" + await transcribe(audio_upload)).strip()
        route.append(f"Speech recognition · {settings.whisper_model or 'local Whisper API'}")

    routing_prompt = message + ("\nThe user selected image generation mode; create an image." if intent == "image" else "")
    steps = await plan(routing_prompt, image_data is not None)
    route.append(f"Router · {settings.router_model}")
    artifacts: list[Artifact] = []
    outputs: list[str] = []
    for specialist in steps:
        if specialist == "vision":
            route.append(f"Vision · {settings.vision_model}")
            reply, found = await generate_text(message or "Describe the attached image.", history, image_data, settings.vision_model)
            outputs.append("Image understanding: " + reply)
            artifacts.extend(found)
        elif specialist == "code":
            route.append(f"Code · {settings.code_model}")
            reply, found = await generate_text(message, history, None, settings.code_model)
            outputs.append(reply)
            artifacts.extend(found)
            if not any(a.type == "code" for a in found) and any(w in message.lower() for w in ("code", "function", "script", "program", "implement", "website", "landing page")):
                artifacts.append(Artifact(id=str(uuid.uuid4()), type="code", title="Code draft", content=reply, language="text"))
        elif specialist == "image_generation":
            route.append(f"Image generation · {settings.image_model}")
            artifacts.append(await generate_image(message))
            outputs.append("The image generation specialist created an image. Describe it briefly and invite the user to open it in the canvas.")
        else:
            route.append(f"Text · {settings.text_model}")
            reply, found = await generate_text(message, history, None, settings.text_model)
            outputs.append(reply)
            artifacts.extend(found)

    route.append(f"Response synthesis · {settings.combiner_model}")
    synthesis_prompt = (
        "Answer the user's request using the specialist results below. Make the answer concise and coherent. "
        "Do not claim work that the results do not support.\n\n"
        f"User request:\n{message}\n\nSpecialist results:\n" + "\n\n".join(outputs)
    )
    final_reply, synthesized = await generate_text(synthesis_prompt, history, None, settings.combiner_model)
    artifacts.extend(synthesized)

    if intent == "audio":
        spoken = await synthesize(final_reply)
        if spoken:
            route.append(f"Speech synthesis · {settings.tts_model}")
            artifacts.append(Artifact(id=str(uuid.uuid4()), type="audio", title="Spoken response", url=spoken))
    return ChatResponse(reply=final_reply, artifacts=artifacts, intent=intent, route=route)

