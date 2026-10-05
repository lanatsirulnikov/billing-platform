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

def build_billing_ai_prompt(facts: list[str], tool_calls: list[dict]) -> str:
    facts_text = "\n".join(f"- {fact}" for fact in facts)
    tool_calls_text = "\n".join(
        f"- {tool_call['name']}: {tool_call['status']} - {tool_call['result']}"
        for tool_call in tool_calls
    )

    return f"""Explain why this customer invoice changed.

Use only these facts:
{facts_text}

Tool calls:
{tool_calls_text}

Return one concise customer-facing explanation.
""".strip()
