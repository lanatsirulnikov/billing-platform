from app.core.settings import get_settings


class BillingAIUnavailable(Exception):
    pass


def ensure_billing_ai_enabled() -> None:
    settings = get_settings()

    if not settings.billing_ai_enabled:
        raise BillingAIUnavailable("Billing AI is disabled")

    if not settings.openai_api_key:
        raise BillingAIUnavailable("OPENAI_API_KEY is not configured")