import pytest
from app.core.settings import get_settings
from app.services.billing_ai import (
    BillingAIUnavailable,
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