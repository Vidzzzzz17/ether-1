from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"
    auth_mode: str = "supabase"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    llm_models: str = "qwen2.5:7b,qwen2.5-coder:7b,qwen2.5vl:7b"
    whisper_model: str = ""
    whisper_api_url: str = ""
    whisper_api_key: str = ""
    tts_api_url: str = ""
    tts_api_key: str = ""
    image_api_url: str = ""
    image_api_key: str = ""
    max_upload_mb: int = 15
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def available_llm_models(self) -> list[str]:
        return [model.strip() for model in self.llm_models.split(",") if model.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

