from decimal import Decimal
from datetime import date

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem


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

    assert data["current_total"] == "124.00"
    assert data["previous_total"] == "99.00"
    assert data["difference"] == "25.00"
    assert "Usage overage increased by 25.00" in data["summary"]
    assert "Current usage overage total: 25.00" in data["facts"]
    assert "Previous usage overage total: 0" in data["facts"]