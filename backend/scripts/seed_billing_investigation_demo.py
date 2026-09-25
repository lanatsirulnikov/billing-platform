from decimal import Decimal
from datetime import date

from app.db.session import SessionLocal
import app.models.init  # noqa: F401

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem


DEMO_CUSTOMER_EMAIL = "billing-investigation-demo@example.com"


def main():
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.email == DEMO_CUSTOMER_EMAIL)
            .one_or_none()
        )

        if customer is None:
            customer = Customer(
                name="Billing Investigation Demo Customer",
                email=DEMO_CUSTOMER_EMAIL,
            )
            db.add(customer)
            db.flush()

        existing_demo_invoices = (
            db.query(Invoice)
            .filter(
                Invoice.customer_id == customer.id,
                Invoice.invoice_number.in_(["DEMO-INV-202605", "DEMO-INV-202606"]),
            )
            .all()
        )

        for invoice in existing_demo_invoices:
            (
                db.query(InvoiceItem)
                .filter(InvoiceItem.invoice_id == invoice.id)
                .delete(synchronize_session=False)
            )
            db.delete(invoice)

        db.flush()

        previous_invoice = Invoice(
            invoice_number="DEMO-INV-202605",
            customer_id=customer.id,
            status="draft",
            due_date=date(2026, 5, 1),
            subtotal=Decimal("99.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("99.00"),
            currency="USD",
        )

        current_invoice = Invoice(
            invoice_number="DEMO-INV-202606",
            customer_id=customer.id,
            status="draft",
            due_date=date(2026, 6, 1),
            subtotal=Decimal("124.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("124.00"),
            currency="USD",
        )

        db.add_all([previous_invoice, current_invoice])
        db.flush()

        db.add_all([
            InvoiceItem(
                invoice_id=previous_invoice.id,
                subscription_id=None,
                item_type="subscription_base",
                description="Previous monthly base charge",
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
                description="Current monthly base charge",
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
                description="Usage overage for additional active users",
                period_start=date(2026, 5, 1),
                period_end=date(2026, 6, 1),
                quantity=5,
                unit_price=Decimal("5.00"),
                amount=Decimal("25.00"),
            ),
        ])

        db.commit()

        print("Demo data created.")
        print(f"customer_id={customer.id}")
        print(f"previous_invoice_id={previous_invoice.id}")
        print(f"current_invoice_id={current_invoice.id}")

    finally:
        db.close()


if __name__ == "__main__":
    main()