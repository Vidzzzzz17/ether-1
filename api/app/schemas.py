from typing import Literal
from pydantic import BaseModel, Field

Intent = Literal["text", "image", "audio"]

class Artifact(BaseModel):
    id: str
    type: Literal["text", "code", "document", "image", "audio"]
    title: str
    content: str = ""
    language: str | None = None
    url: str | None = None

class ChatResponse(BaseModel):
    reply: str
    artifacts: list[Artifact] = Field(default_factory=list)
    intent: Intent

