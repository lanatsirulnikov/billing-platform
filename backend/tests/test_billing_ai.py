import pytest

from app.services.billing_ai import BillingAIUnavailable, ensure_billing_ai_enabled


def test_billing_ai_disabled_by_default():
    with pytest.raises(BillingAIUnavailable, match="Billing AI is disabled"):
        ensure_billing_ai_enabled()