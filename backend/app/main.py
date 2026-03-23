from fastapi import FastAPI
from app.api.customers import router as customers_router

from app.core.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(customers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}