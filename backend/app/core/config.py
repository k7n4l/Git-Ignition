
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Git Ignition"
    env: str = "development"
    github_token: str = ""
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    index_max_files: int = 50
    db_path: str = "data/rag.db"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
