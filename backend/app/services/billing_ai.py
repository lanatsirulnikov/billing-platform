from app.core.settings import get_settings


class BillingAIUnavailable(Exception):
    pass


def ensure_billing_ai_enabled() -> None:
    settings = get_settings()

    if not settings.billing_ai_enabled:
        raise BillingAIUnavailable("Billing AI is disabled")

    if not settings.openai_api_key:
        raise BillingAIUnavailable("OPENAI_API_KEY is not configured")

def explain_invoice_increase_with_ai(facts: list[str], tool_calls: list[dict]) -> str:
    ensure_billing_ai_enabled()

    # TODO: Replace this deterministic placeholder with an OpenAI Responses API call.
    facts_text = " ".join(facts)

    if "Usage overage" in facts_text or "usage overage" in facts_text:
        return "AI explanation: invoice increased because usage overage increased."

    if "subscription base" in facts_text:
        return "AI explanation: invoice increased because subscription base charges increased."

    return "AI explanation: invoice changed based on the retrieved billing records."