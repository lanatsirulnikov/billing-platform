from fastapi import FastAPI
from app.api.customers import router as customers_router
from app.api.plans import router as plans_router
from app.api.subscriptions import router as subscriptions_router
from app.api.invoices import router as invoices_router
from app.api.invoice_items import router as invoice_items_router
from app.core.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.include_router(customers_router)
app.include_router(plans_router)
app.include_router(subscriptions_router)
app.include_router(invoices_router)
app.include_router(invoice_items_router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}