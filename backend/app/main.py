from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import health,github,parser

app = FastAPI(title=settings.app_name)
app.include_router(health.router)
app.include_router(github.router)
app.include_router(parser.router)
