import pytest
from app.core.settings import get_settings
from app.services.billing_ai import (
    BillingAIUnavailable,
    build_billing_ai_prompt,
    ensure_billing_ai_enabled,
    explain_invoice_increase_with_ai,
)


def test_billing_ai_disabled_by_default():
    with pytest.raises(BillingAIUnavailable, match="Billing AI is disabled"):
        ensure_billing_ai_enabled()

def test_ai_explanation_placeholder_uses_facts(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "billing_ai_enabled", True)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    summary = explain_invoice_increase_with_ai(
        facts=["Current usage overage total: 25.00"],
        tool_calls=[],
    )

    assert summary == "AI explanation: invoice increased because usage overage increased."

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