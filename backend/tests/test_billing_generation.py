from datetime import date
from decimal import Decimal

from app.models.customer import Customer
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.services.invoicing import autogenerate_invoices
from app.models.invoice import Invoice
from app.models.subscription import Subscription


def test_active_subscription_creates_base_item_and_advances_next_billing_date(db_session):
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    plan = Plan(
        name="Test Monthly",
        price=Decimal("99.00"),
        user_quota=9,
        overage_user_price=Decimal("9.00"),
        interval="monthly",
    )
    db_session.add(plan)
    db_session.flush()

    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        price=Decimal("99.00"),
        user_quota_override=None,
        overage_user_price_override=None,
        status="active",
        start_date=date(2026, 5, 1),
        end_date=None,
        next_billing_date=date(2026, 6, 1),
        is_billable=True,
    )
    db_session.add(subscription)
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).one()
    items = db_session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()
    db_session.refresh(subscription)

    assert len(items) == 1
    assert items[0].item_type == "subscription_base"
    assert items[0].amount == Decimal("99.00")
    assert subscription.next_billing_date == date(2026, 7, 1)
    assert subscription.is_billable is True

def test_duplicate_protection_on_subscription_base(db_session):
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    plan = Plan(
        name="Test Monthly",
        price=Decimal("89.00"),
        user_quota=8,
        overage_user_price=Decimal("8.00"),
        interval="monthly",
    )
    db_session.add(plan)
    db_session.flush()

    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        price=Decimal("89.00"),
        user_quota_override=None,
        overage_user_price_override=None,
        status="active",
        start_date=date(2026, 5, 1),
        end_date=None,
        next_billing_date=date(2026, 6, 1),
        is_billable=True,
    )
    db_session.add(subscription)
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(subscription)

    subscription.next_billing_date = date(2026, 6, 1)
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(subscription)

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).one()
    items = db_session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()

    assert len(items) == 1
    assert items[0].item_type == "subscription_base"
    assert invoice.subtotal == Decimal("89.00")
    assert invoice.total_amount == Decimal("89.00")
    assert subscription.is_billable is True

def test_subscription_with_missing_plan_is_marked_unbillable(db_session):
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    subscription = Subscription(
        customer_id=customer.id,
        plan_id="00000000-0000-0000-0000-000000000999",
        price=Decimal("89.00"),
        user_quota_override=None,
        overage_user_price_override=None,
        status="active",
        start_date=date(2026, 5, 1),
        end_date=None,
        next_billing_date=date(2026, 6, 1),
        is_billable=True,
    )
    db_session.add(subscription)
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(subscription)

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).first()
    assert invoice is None
    assert subscription.is_billable is False
