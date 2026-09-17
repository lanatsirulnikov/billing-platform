import pytest

from datetime import date
from decimal import Decimal

from app.models.customer import Customer
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.usage_record import UsageRecord

from app.services import invoicing
from app.services.invoicing import autogenerate_invoices

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

def test_paused_subscription_creates_final_base_item_and_stops_billing(db_session):
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
        status="paused",
        start_date=date(2026, 5, 1),
        end_date=None,
        next_billing_date=date(2026, 6, 1),
        is_billable=True,
    )
    db_session.add(subscription)
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(subscription)

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(subscription)

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).one()
    items = db_session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()

    assert len(items) == 1
    assert items[0].item_type == "subscription_base"
    assert items[0].period_start == date(2026, 5, 1)
    assert items[0].period_end == date(2026, 6, 1)
    assert items[0].amount == Decimal("89.00")
    assert subscription.next_billing_date == date(2026, 6, 1)
    assert subscription.is_billable is False

def test_usage_overage_creates_overage_item_with_correct_amount(db_session):
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    plan = Plan(
        name="Test Monthly",
        price=Decimal("100.00"),
        user_quota=10,
        overage_user_price=Decimal("5.00"),
        interval="monthly",
    )
    db_session.add(plan)
    db_session.flush()

    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        price=Decimal("100.00"),
        user_quota_override=None,
        overage_user_price_override=None,
        status="active",
        start_date=date(2026, 5, 1),
        end_date=None,
        next_billing_date=date(2026, 6, 1),
        is_billable=True,
    )
    db_session.add(subscription)
    db_session.flush()

    db_session.add_all([
        UsageRecord(
            subscription_id=subscription.id,
            recorded_on=date(2026, 5, 10),
            active_user_count=12,
        ),
        UsageRecord(
            subscription_id=subscription.id,
            recorded_on=date(2026, 5, 20),
            active_user_count=15,
        ),
        UsageRecord(
            subscription_id=subscription.id,
            recorded_on=date(2026, 6, 1),
            active_user_count=99,
        ),
    ])
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).one()
    items = db_session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()

    overage_item = next(item for item in items if item.item_type == "usage_overage")
    base_item = next(item for item in items if item.item_type == "subscription_base")

    assert len(items) == 2
    assert base_item.amount == Decimal("100.00")
    assert overage_item.period_start == date(2026, 5, 1)
    assert overage_item.period_end == date(2026, 6, 1)
    assert overage_item.quantity == 5
    assert overage_item.unit_price == Decimal("5.00")
    assert overage_item.amount == Decimal("25.00")
    assert invoice.subtotal == Decimal("125.00")
    assert invoice.total_amount == Decimal("125.00")

def test_month_end_subscription_advances_from_february_to_march(db_session):
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    plan = Plan(
        name="Test Monthly",
        price=Decimal("75.00"),
        user_quota=7,
        overage_user_price=Decimal("7.00"),
        interval="monthly",
    )
    db_session.add(plan)
    db_session.flush()

    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        price=Decimal("75.00"),
        user_quota_override=None,
        overage_user_price_override=None,
        status="active",
        start_date=date(2026, 1, 29),
        end_date=None,
        next_billing_date=date(2026, 2, 28),
        is_billable=True,
    )
    db_session.add(subscription)
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 2, 28))
    db_session.refresh(subscription)

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).one()
    item = db_session.query(InvoiceItem).filter_by(invoice_id=invoice.id).one()

    assert item.period_start == date(2026, 1, 29)
    assert item.period_end == date(2026, 2, 28)
    assert item.amount == Decimal("75.00")
    assert subscription.next_billing_date == date(2026, 3, 28)

def test_multiple_subscriptions_for_one_customer_create_one_invoice_with_multiple_items(db_session):
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    basic_plan = Plan(
        name="Basic Monthly",
        price=Decimal("50.00"),
        user_quota=5,
        overage_user_price=Decimal("5.00"),
        interval="monthly",
    )
    pro_plan = Plan(
        name="Pro Monthly",
        price=Decimal("120.00"),
        user_quota=20,
        overage_user_price=Decimal("10.00"),
        interval="monthly",
    )
    db_session.add_all([basic_plan, pro_plan])
    db_session.flush()

    basic_subscription = Subscription(
        customer_id=customer.id,
        plan_id=basic_plan.id,
        price=Decimal("50.00"),
        user_quota_override=None,
        overage_user_price_override=None,
        status="active",
        start_date=date(2026, 5, 1),
        end_date=None,
        next_billing_date=date(2026, 6, 1),
        is_billable=True,
    )
    pro_subscription = Subscription(
        customer_id=customer.id,
        plan_id=pro_plan.id,
        price=Decimal("120.00"),
        user_quota_override=None,
        overage_user_price_override=None,
        status="active",
        start_date=date(2026, 5, 1),
        end_date=None,
        next_billing_date=date(2026, 6, 1),
        is_billable=True,
    )
    db_session.add_all([basic_subscription, pro_subscription])
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(basic_subscription)
    db_session.refresh(pro_subscription)

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).one()
    items = db_session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()

    assert len(items) == 2
    assert {item.subscription_id for item in items} == {
        basic_subscription.id,
        pro_subscription.id,
    }
    assert {item.amount for item in items} == {
        Decimal("50.00"),
        Decimal("120.00"),
    }
    assert invoice.subtotal == Decimal("170.00")
    assert invoice.total_amount == Decimal("170.00")
    assert basic_subscription.next_billing_date == date(2026, 7, 1)
    assert pro_subscription.next_billing_date == date(2026, 7, 1)

def test_invoice_generation_rolls_back_when_item_processing_fails(db_session, monkeypatch):
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    plan = Plan(
        name="Test Monthly",
        price=Decimal("90.00"),
        user_quota=9,
        overage_user_price=Decimal("9.00"),
        interval="monthly",
    )
    db_session.add(plan)
    db_session.flush()

    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        price=Decimal("90.00"),
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

    subscription_id = subscription.id
    customer_id = customer.id

    def fail_recalculate_totals(db, invoice, invoice_item):
        raise RuntimeError("simulated billing failure")

    monkeypatch.setattr(invoicing, "recalculate_totals", fail_recalculate_totals)

    with pytest.raises(RuntimeError, match="simulated billing failure"):
        autogenerate_invoices(db_session, date(2026, 6, 1))

    subscription_after_failure = db_session.get(Subscription, subscription_id)

    invoice = db_session.query(Invoice).filter_by(customer_id=customer_id).first()
    items = db_session.query(InvoiceItem).filter_by(subscription_id=subscription_id).all()

    assert invoice is None
    assert items == []
    assert subscription_after_failure.next_billing_date == date(2026, 6, 1)
    assert subscription_after_failure.is_billable is True

def test_cancelled_subscription_creates_final_base_item_and_stops_billing(db_session):
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
        status="cancelled",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 20),
        next_billing_date=date(2026, 6, 1),
        is_billable=True,
    )
    db_session.add(subscription)
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(subscription)

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(subscription)

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).one()
    items = db_session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()

    assert len(items) == 1
    assert items[0].item_type == "subscription_base"
    assert items[0].period_start == date(2026, 5, 1)
    assert items[0].period_end == date(2026, 6, 1)
    assert items[0].amount == Decimal("89.00")
    assert subscription.next_billing_date == date(2026, 6, 1)
    assert subscription.is_billable is False

def test_zero_overrides_inherit_plan_values(db_session):
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
        user_quota_override=0,
        overage_user_price_override=Decimal("0.00"),
        status="active",
        start_date=date(2026, 5, 1),
        next_billing_date=date(2026, 6, 1),
        is_billable=True,
    )
    db_session.add(subscription)
    db_session.commit()

    db_session.add_all([
        UsageRecord(
            subscription_id=subscription.id,
            recorded_on=date(2026, 5, 20),
            active_user_count=10,
        )
    ])
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(subscription)

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).one()
    items = db_session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()

    base_item = next(item for item in items if item.item_type == "subscription_base")
    overage_item = next(item for item in items if item.item_type == "usage_overage")

    assert len(items) == 2
    assert base_item.amount == Decimal("89.00")
    assert overage_item.period_start == date(2026, 5, 1)
    assert overage_item.period_end == date(2026, 6, 1)
    assert overage_item.quantity == 2
    assert overage_item.unit_price == Decimal("8.00")
    assert overage_item.amount == Decimal("16.00")
    assert invoice.subtotal == Decimal("105.00")
    assert invoice.total_amount == Decimal("105.00")
    assert subscription.next_billing_date == date(2026, 7, 1)
    assert subscription.is_billable is True

def test_overdue_subscription_advances_one_interval_per_generation_run(db_session):
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
        start_date=date(2026, 3, 1),
        end_date=None,
        next_billing_date=date(2026, 4, 1),
        is_billable=True,
    )
    db_session.add(subscription)
    db_session.commit()

    autogenerate_invoices(db_session, date(2026, 6, 1))
    db_session.refresh(subscription)

    invoice = db_session.query(Invoice).filter_by(customer_id=customer.id).one()
    item = db_session.query(InvoiceItem).filter_by(invoice_id=invoice.id).one()

    assert item.period_start == date(2026, 3, 1)
    assert item.period_end == date(2026, 4, 1)
    assert item.amount == Decimal("89.00")
    assert subscription.next_billing_date == date(2026, 5, 1)
    assert subscription.is_billable is True