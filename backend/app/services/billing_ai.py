import logging

from app.core.settings import get_settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class BillingAIUnavailable(Exception):
    pass


class BillingAIError(Exception):
    pass


def ensure_billing_ai_enabled() -> None:
    settings = get_settings()

    if not settings.billing_ai_enabled:
        raise BillingAIUnavailable("Billing AI is disabled")

    if not settings.openai_api_key:
        raise BillingAIUnavailable("OPENAI_API_KEY is not configured")

def explain_invoice_increase_with_ai(facts: list[str], tool_calls: list[dict]) -> str:
    ensure_billing_ai_enabled()
    prompt = build_billing_ai_prompt(facts=facts, tool_calls=tool_calls)
    return call_openai_for_invoice_explanation(prompt)

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

def call_openai_for_invoice_explanation(prompt: str) -> str:
    settings = get_settings()

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(
            model=settings.billing_ai_model,
            input=prompt,
        )
        
    except Exception as exc:
        logger.warning("AI invoice explanation failed: %s", exc)
        raise BillingAIError("Billing AI explanation failed") from exc

    return response.output_text
