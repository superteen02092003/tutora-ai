from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    gemini_api_key: str
    # Key RIÊNG cho tính năng lớp học
    gemini_classroom_key: str = ""
    supabase_url: str
    supabase_key: str
    supabase_dev_url: str = ""
    supabase_dev_key: str = ""
    api_key: str
    docs_username: str = "tutora-ap"
    docs_password: str
    # "BAAI/bge-m3" — tốt hơn nhưng ~570MB, dùng khi có VPS riêng
    embed_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    rag_top_k: int = 3
    rag_embedding_dim: int = 768
    env: str = "development"
    # Sinh chữ đi qua OpenAI (app/core/llm.py) từ 2026-11-11; Gemini chỉ còn cho embedding.
    openai_api_key: str = ""
    llm_model: str = "gpt-6-luna"
    # Trợ lý web cần trả lời nhanh: Gemini Flash-Lite ~1 s/lượt, gpt-6-luna ~4 s (đo 2026-11-11).
    assistant_model: str = "gemini-3.5-flash-lite"
    solve_model: str = "gpt-6-luna"
    solve_thinking_model: str = "gpt-6-luna"
    dotnet_be_url: str = "http://localhost:5166"

    @field_validator("dotnet_be_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
