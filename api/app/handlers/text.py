import base64, json, re, uuid
import httpx
from ..config import get_settings
from ..schemas import Artifact

SYSTEM = "You are a helpful multimodal assistant. Answer clearly. If useful, create editable side-panel artefacts. Return ONLY valid JSON with keys reply (string) and artifacts (array). Each artifact has type (text|code|document), title, content, and optional language. Do not wrap JSON in markdown fences."

async def generate_text(prompt: str, history: list[dict] | None = None, image: tuple[bytes, str] | None = None, model: str | None = None) -> tuple[str, list[Artifact]]:
    settings = get_settings()
    messages = [{"role": "system", "content": SYSTEM}]
    for item in (history or [])[-12:]:
        if item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str): messages.append({"role": item["role"], "content": item["content"][:8000]})
    user_content: str | list[dict] = prompt
    if image:
        encoded = base64.b64encode(image[0]).decode("ascii")
        user_content = [{"type":"text","text":prompt or "Describe this image."},{"type":"image_url","image_url":{"url":f"data:{image[1]};base64,{encoded}"}}]
    messages.append({"role":"user","content":user_content})
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(settings.llm_base_url.rstrip("/")+"/chat/completions", headers={"Authorization":f"Bearer {settings.llm_api_key}"}, json={"model":model or settings.llm_model,"messages":messages,"temperature":0.4})
            response.raise_for_status(); raw=response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError,KeyError,IndexError,ValueError) as exc: raise RuntimeError("Text model request failed. Check the configured OpenAI-compatible endpoint.") from exc
    try:
        payload=json.loads(re.sub(r"^```(?:json)?\s*|\s*```$","",raw.strip(),flags=re.I)); reply=str(payload.get("reply","")); artifacts=[]
        for item in payload.get("artifacts",[])[:6]:
            if item.get("type") in ("text","code","document"):
                artifacts.append(Artifact(id=str(uuid.uuid4()),type=item["type"],title=str(item.get("title","Untitled"))[:120],content=str(item.get("content",""))[:50000],language=item.get("language")))
        return reply or raw,artifacts
    except (json.JSONDecodeError,AttributeError,TypeError): return raw,[]

