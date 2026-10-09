import pytest
from app.core.settings import get_settings
from app.services.billing_ai import (
    BillingAIUnavailable,
    build_billing_ai_prompt,
    ensure_billing_ai_enabled,
    explain_invoice_increase_with_ai,
)


def test_billing_ai_disabled_by_default(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "billing_ai_enabled", False)
    monkeypatch.setattr(settings, "openai_api_key", None)
    with pytest.raises(BillingAIUnavailable, match="Billing AI is disabled"):
        ensure_billing_ai_enabled()


def test_ai_explanation_calls_openai_with_built_prompt(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "billing_ai_enabled", True)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "billing_ai_model", "test-model")

    captured = {}

    def fake_call_openai(prompt: str) -> str:
        captured["prompt"] = prompt
        return "AI explanation from mocked OpenAI."

    monkeypatch.setattr(
        "app.services.billing_ai.call_openai_for_invoice_explanation",
        fake_call_openai,
    )

    summary = explain_invoice_increase_with_ai(
        facts=["Current invoice total: 124.00"],
        tool_calls=[
            {
                "name": "fetch_current_invoice",
                "status": "success",
                "result": "Found invoice DEMO-INV-202606",
            }
        ],
    )

    assert summary == "AI explanation from mocked OpenAI."
    assert "Current invoice total: 124.00" in captured["prompt"]
    assert "fetch_current_invoice: success - Found invoice DEMO-INV-202606" in captured["prompt"]

def test_build_billing_ai_prompt_includes_facts_and_tool_calls():
    prompt = build_billing_ai_prompt(
        facts=["Current invoice total: 124.00", "Previous invoice total: 99.00"],
        tool_calls=[
            {
                "name": "fetch_current_invoice",
                "status": "success",
                "result": "Found invoice DEMO-INV-202606",
            }
        ],
    )

    assert "Current invoice total: 124.00" in prompt
    assert "Previous invoice total: 99.00" in prompt
    assert "fetch_current_invoice: success - Found invoice DEMO-INV-202606" in prompt
    assert "Return one concise customer-facing explanation." in prompt