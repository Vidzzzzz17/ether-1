"""Local task planner for Ether 1. The router itself is an Ollama model role."""
import json
import re

import httpx

from .config import get_settings

SPECIALISTS = {"text", "code", "vision", "image_generation"}


def _fallback_plan(prompt: str, has_image: bool) -> list[str]:
    lower = prompt.lower()
    steps: list[str] = []
    if has_image:
        steps.append("vision")
    if any(word in lower for word in ("generate an image", "create an image", "draw ", "make an image", "illustration of")):
        steps.append("image_generation")
    elif any(word in lower for word in ("code", "program", "function", "script", "debug", "website", "landing page", "implement")):
        steps.append("code")
    else:
        steps.append("text")
    return list(dict.fromkeys(steps))[:3]


async def plan(prompt: str, has_image: bool) -> list[str]:
    """Ask the local router to select skills; fall back when it is not available."""
    settings = get_settings()
    system = (
        "You are Ether 1's task router. Select specialist steps for the request. "
        "Available specialists: text (reasoning/writing), code (software/code), "
        "vision (understand an attached image), image_generation (create an image). "
        "Return only JSON: {\"steps\":[\"text\"]}. Include vision when an image is attached. "
        "Choose at most 3 distinct steps. Do not answer the user."
    )
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                settings.llm_base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={"model": settings.router_model, "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps({"request": prompt, "image_attached": has_image})},
                ], "response_format": {"type": "json_object"}, "temperature": 0},
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I))
        steps = [step for step in payload.get("steps", []) if step in SPECIALISTS]
        if has_image and "vision" not in steps:
            steps.insert(0, "vision")
        return list(dict.fromkeys(steps))[:3] or _fallback_plan(prompt, has_image)
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError):
        return _fallback_plan(prompt, has_image)

