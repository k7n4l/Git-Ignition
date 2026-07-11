from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name : str = "Git Ignition"
    env : str = "development"
    github_token: str = ""

    class Config:
        env_file = ".env"

settings = Settings()