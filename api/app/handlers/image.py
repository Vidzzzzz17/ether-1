import uuid
import httpx
from fastapi import HTTPException
from ..config import get_settings
from ..schemas import Artifact

async def generate_image(prompt: str) -> Artifact:
    settings=get_settings()
    if not settings.image_api_url: raise HTTPException(status_code=503,detail="Configure IMAGE_API_URL to enable image generation.")
    headers={"Authorization":f"Bearer {settings.image_api_key}"} if settings.image_api_key else {}
    async with httpx.AsyncClient(timeout=180) as client:
        response=await client.post(settings.image_api_url,headers=headers,json={"prompt":prompt,"n":1,"size":"1024x1024"});response.raise_for_status()
    item=response.json().get("data",[{}])[0]
    if item.get("url"):return Artifact(id=str(uuid.uuid4()),type="image",title="Generated image",url=item["url"])
    if item.get("b64_json"):return Artifact(id=str(uuid.uuid4()),type="image",title="Generated image",url="data:image/png;base64,"+item["b64_json"])
    raise HTTPException(status_code=502,detail="Image provider returned no image URL or image data.")

