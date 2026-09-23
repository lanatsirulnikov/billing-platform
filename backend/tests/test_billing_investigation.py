from decimal import Decimal
from datetime import date

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.services.billing_investigation import (
    BILLING_INVESTIGATION_PROMPT,
    PROMPT_VERSION,
)

def test_billing_investigation_prompt_is_versioned():
    assert PROMPT_VERSION == "billing-investigation-v1"
    assert "read-only billing investigation assistant" in BILLING_INVESTIGATION_PROMPT
    assert "Do not modify billing data" in BILLING_INVESTIGATION_PROMPT

def test_invoice_increase_investigation_explains_usage_overage(client, db_session):
    customer = Customer(
        name="Investigation Customer",
        email="investigation@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    previous_invoice = Invoice(
        invoice_number="INV-202605-001",
        customer_id=customer.id,
        status="draft",
        due_date=date(2026, 5, 1),
        subtotal=Decimal("99.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("99.00"),
        currency="USD",
    )
    current_invoice = Invoice(
        invoice_number="INV-202606-001",
        customer_id=customer.id,
        status="draft",
        due_date=date(2026, 6, 1),
        subtotal=Decimal("124.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("124.00"),
        currency="USD",
    )
    db_session.add_all([previous_invoice, current_invoice])
    db_session.flush()

    db_session.add_all([
        InvoiceItem(
            invoice_id=previous_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Previous base charge",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 5, 1),
            quantity=1,
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
        ),
        InvoiceItem(
            invoice_id=current_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Current base charge",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 6, 1),
            quantity=1,
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
        ),
        InvoiceItem(
            invoice_id=current_invoice.id,
            subscription_id=None,
            item_type="usage_overage",
            description="Current usage overage",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 6, 1),
            quantity=5,
            unit_price=Decimal("5.00"),
            amount=Decimal("25.00"),
        ),
    ])
    db_session.commit()

    response = client.post(
        "/billing-investigations/invoice-increase",
        json={
            "customer_id": customer.id,
            "previous_invoice_id": previous_invoice.id,
            "current_invoice_id": current_invoice.id,
        },
    )

    assert response.status_code == 200
    data = response.json()
    tool_names = [tool["name"] for tool in data["tool_calls"]]

    assert data["current_total"] == "124.00"
    assert data["previous_total"] == "99.00"
    assert data["difference"] == "25.00"
    assert "Usage overage increased by 25.00" in data["summary"]
    assert "Current usage overage total: 25.00" in data["facts"]
    assert "Previous usage overage total: 0" in data["facts"]
    assert "fetch_current_invoice" in tool_names
    assert "fetch_previous_invoice" in tool_names
    assert "compare_invoice_totals" in tool_names
    assert "fetch_current_invoice_items" in tool_names
    assert "fetch_previous_invoice_items" in tool_names
    assert "compare_charge_categories" in tool_names
    assert len(data["tool_calls"]) <= 6
    assert data["prompt_version"] == "billing-investigation-v1"

def test_missing_invoice(client, db_session):
    customer = Customer(
        name="Investigation Customer",
        email="investigation@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    current_invoice = Invoice(
        invoice_number="INV-202606-001",
        customer_id=customer.id,
        status="draft",
        due_date=date(2026, 6, 1),
        subtotal=Decimal("124.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("124.00"),
        currency="USD",
    )
    db_session.add(current_invoice)
    db_session.flush()

    db_session.add(
            InvoiceItem(
            invoice_id=current_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Current base charge",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 6, 1),
            quantity=1,
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
        ))
    db_session.commit()

    response = client.post(
        "/billing-investigations/invoice-increase",
        json={
            "customer_id": customer.id,
            "previous_invoice_id": "00000000-0000-0000-0000-000000000999",
            "current_invoice_id": current_invoice.id,
        },
    )

    assert response.status_code == 404
    data = response.json()

    assert "One or both invoices not found" in data["detail"]

def test_different_customer_invoices(client, db_session):
    customer1 = Customer(
        name="Investigation Customer 1",
        email="investigation1@example.com",
    )
    db_session.add(customer1)
    db_session.flush()

    customer2 = Customer(
            name="Investigation Customer 2",
            email="investigation2@example.com",
        )
    db_session.add(customer2)
    db_session.flush()

    previous_invoice = Invoice(
        invoice_number="INV-202605-001",
        customer_id=customer1.id,
        status="draft",
        due_date=date(2026, 5, 1),
        subtotal=Decimal("99.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("99.00"),
        currency="USD",
    )
    current_invoice = Invoice(
        invoice_number="INV-202606-001",
        customer_id=customer2.id,
        status="draft",
        due_date=date(2026, 6, 1),
        subtotal=Decimal("124.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("124.00"),
        currency="USD",
    )
    db_session.add_all([previous_invoice, current_invoice])
    db_session.flush()

    db_session.add_all([
        InvoiceItem(
            invoice_id=previous_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Previous base charge",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 5, 1),
            quantity=1,
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
        ),
        InvoiceItem(
            invoice_id=current_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Current base charge",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 6, 1),
            quantity=1,
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
        )
    ])
    db_session.commit()

    response = client.post(
        "/billing-investigations/invoice-increase",
        json={
            "customer_id": customer2.id,
            "previous_invoice_id": previous_invoice.id,
            "current_invoice_id": current_invoice.id,
        },
    )

    assert response.status_code == 400
    data = response.json()

    assert "Invoices must belong to the requested customer" in data["detail"]

def test_invoice_increase_investigation_explains_new_subscription_charge(client, db_session):
    customer = Customer(
        name="Investigation Customer",
        email="new-subscription@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    previous_invoice = Invoice(
        invoice_number="INV-202605-NEW-001",
        customer_id=customer.id,
        status="draft",
        due_date=date(2026, 5, 1),
        subtotal=Decimal("99.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("99.00"),
        currency="USD",
    )
    current_invoice = Invoice(
        invoice_number="INV-202606-NEW-001",
        customer_id=customer.id,
        status="draft",
        due_date=date(2026, 6, 1),
        subtotal=Decimal("149.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("149.00"),
        currency="USD",
    )
    db_session.add_all([previous_invoice, current_invoice])
    db_session.flush()

    db_session.add_all([
        InvoiceItem(
            invoice_id=previous_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Main subscription",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 5, 1),
            quantity=1,
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
        ),
        InvoiceItem(
            invoice_id=current_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Main subscription",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 6, 1),
            quantity=1,
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
        ),
        InvoiceItem(
            invoice_id=current_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Additional subscription",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 6, 1),
            quantity=1,
            unit_price=Decimal("50.00"),
            amount=Decimal("50.00"),
        ),
    ])
    db_session.commit()

    response = client.post(
        "/billing-investigations/invoice-increase",
        json={
            "customer_id": customer.id,
            "previous_invoice_id": previous_invoice.id,
            "current_invoice_id": current_invoice.id,
        },
    )

    assert response.status_code == 200
    data = response.json()
    tool_names = [tool["name"] for tool in data["tool_calls"]]

    assert data["difference"] == "50.00"
    assert "Subscription base charges increased by 50.00" in data["summary"]
    assert "Current invoice total: 149.00" in data["facts"]
    assert "Previous invoice total: 99.00" in data["facts"]
    assert "fetch_current_invoice" in tool_names
    assert "compare_charge_categories" in tool_names
    assert data["prompt_version"] == "billing-investigation-v1"
    
def test_no_invoice_increase(client, db_session):
    customer = Customer(
        name="Investigation Customer",
        email="new-subscription@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    previous_invoice = Invoice(
        invoice_number="INV-202605-NEW-001",
        customer_id=customer.id,
        status="draft",
        due_date=date(2026, 5, 1),
        subtotal=Decimal("99.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("99.00"),
        currency="USD",
    )
    current_invoice = Invoice(
        invoice_number="INV-202606-NEW-001",
        customer_id=customer.id,
        status="draft",
        due_date=date(2026, 6, 1),
        subtotal=Decimal("99.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("99.00"),
        currency="USD",
    )
    db_session.add_all([previous_invoice, current_invoice])
    db_session.flush()

    db_session.add_all([
        InvoiceItem(
            invoice_id=previous_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Main subscription",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 5, 1),
            quantity=1,
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
        ),
        InvoiceItem(
            invoice_id=current_invoice.id,
            subscription_id=None,
            item_type="subscription_base",
            description="Main subscription",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 6, 1),
            quantity=1,
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
        ),
    ])
    db_session.commit()

    response = client.post(
        "/billing-investigations/invoice-increase",
        json={
            "customer_id": customer.id,
            "previous_invoice_id": previous_invoice.id,
            "current_invoice_id": current_invoice.id,
        },
    )

    assert response.status_code == 200
    data = response.json()
    tool_names = [tool["name"] for tool in data["tool_calls"]]

    assert data["difference"] == "0.00"
    assert "Invoice total did not increase." in data["summary"]
    assert "Current invoice total: 99.00" in data["facts"]
    assert "Previous invoice total: 99.00" in data["facts"]
    assert "fetch_current_invoice" in tool_names
    assert data["prompt_version"] == "billing-investigation-v1"
