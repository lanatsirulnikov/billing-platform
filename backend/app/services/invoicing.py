from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.plan import Plan
from app.models.invoice_counter import InvoiceCounter
from app.models.usage_record import UsageRecord
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from collections import defaultdict

def group_due_subscriptions_by_customer(db: Session, run_date: date):
    grouped = defaultdict(list)

    due_subscriptions = db.scalars(
        select(Subscription).where(
            Subscription.is_billable.is_(True),
            Subscription.next_billing_date <= run_date,
        )
    ).all()

    for subscription in due_subscriptions:
        grouped[subscription.customer_id].append(subscription)

    return dict(grouped)

def autogenerate_invoices(db: Session, run_date: date):
        due_subscriptions_by_customer = group_due_subscriptions_by_customer(db, run_date)

        for customer_id, subscriptions in due_subscriptions_by_customer.items():
            try:
                invoice = None
            
                for subscription in subscriptions:
                    plan = db.get(Plan, subscription.plan_id)
                    if not plan:
                        subscription.is_billable = False
                        continue
                        continue

                    billing_interval = get_billing_interval(plan.interval)
                    current_cycle = get_billing_periods(subscription.next_billing_date, billing_interval)
                    existing_usage_overage_item = get_existing_usage_overage_item(
                        db,
                        subscription.id,
                        current_cycle
                    )
                    existing_subscription_base_item = get_existing_subscription_base_item(
                        db,
                        subscription.id,
                        current_cycle
                    )

                    if not existing_usage_overage_item:
                        included_quota = get_included_quota(subscription, plan)
                        actual_usage = get_max_usage_for_period(
                            db,
                            subscription.id,
                            current_cycle
                        )
                        excess_users = calculate_excess_users(actual_usage, included_quota)

                        if excess_users > 0:
                            if invoice is None:
                                invoice = get_or_create_draft_invoice(db, customer_id, run_date)

                            values = build_invoice_item_values(subscription, plan, "usage_overage", excess_users)
                            invoice_item = add_invoice_item(
                                db,
                                invoice,
                                subscription,
                                "usage_overage",
                                current_cycle["period_start"],
                                current_cycle["period_end"],
                                values["description"],
                                values["quantity"],
                                values["unit_price"],
                                values["amount"]
                            )
                            recalculate_totals(db, invoice, invoice_item)

                    # Use a billing-event state model later
                    if existing_subscription_base_item:
                        finalize_subscription_cycle(subscription, billing_interval)
                    else:
                        if invoice is None:
                            invoice = get_or_create_draft_invoice(db, customer_id, run_date)

                        values = build_invoice_item_values(subscription, plan, "subscription_base")
                        invoice_item = add_invoice_item(
                            db,
                            invoice,
                            subscription,
                            "subscription_base",
                            current_cycle["period_start"],
                            current_cycle["period_end"],
                            values["description"],
                            values["quantity"],
                            values["unit_price"],
                            values["amount"]
                        )
                        recalculate_totals(db, invoice, invoice_item)

                        finalize_subscription_cycle(subscription, billing_interval)
                
                db.commit()

            except Exception:
                db.rollback()
                raise

def add_invoice_item(
    db: Session,
    invoice: Invoice,
    subscription: Subscription,
    item_type: str,
    period_start: date,
    period_end: date,
    description: str,
    quantity: int,
    unit_price: Decimal,
    amount: Decimal,
):
    invoice_item = InvoiceItem(
        invoice_id=invoice.id,
        subscription_id=subscription.id,
        item_type=item_type,
        description=description,
        period_start=period_start,
        period_end=period_end,
        quantity=quantity,
        unit_price=unit_price,
        amount=amount,
    )
    db.add(invoice_item)
    db.flush()
    return invoice_item

def recalculate_totals(db: Session, invoice: Invoice, invoice_item: InvoiceItem):
    subtotal = invoice.subtotal + invoice_item.amount if invoice.subtotal else invoice_item.amount
    invoice.subtotal = subtotal
    invoice.total_amount = invoice.subtotal + (invoice.tax_amount or Decimal("0.00"))
    db.flush()

def get_billing_interval(interval: str):
    if interval == "monthly":
        return relativedelta(months=1)
    if interval == "yearly":
        return relativedelta(years=1)
    if interval == "weekly":
        return relativedelta(weeks=1)
    
    raise ValueError(f"Unsupported billing interval: {interval}")

def get_existing_subscription_base_item(
    db: Session,
    subscription_id: str,
    current_cycle: dict,
):
    return db.scalar(
        select(InvoiceItem).where(
            InvoiceItem.subscription_id == subscription_id,
            InvoiceItem.item_type == "subscription_base",
            InvoiceItem.period_start == current_cycle["period_start"],
            InvoiceItem.period_end == current_cycle["period_end"],
        )
    )

def finalize_subscription_cycle(subscription: Subscription, billing_interval) -> None:
    # Paused/cancelled subscriptions finish the current accounted cycle, then stop billing.
    if subscription.status == "active":
        subscription.next_billing_date = subscription.next_billing_date + billing_interval
    elif subscription.status in {"paused", "cancelled"}:
        subscription.is_billable = False

def get_existing_usage_overage_item(
    db: Session,
    subscription_id: str,
    current_cycle: dict
):
    return db.scalar(
        select(InvoiceItem).where(
            InvoiceItem.subscription_id == subscription_id,
            InvoiceItem.item_type == "usage_overage",
            InvoiceItem.period_start == current_cycle["period_start"],
            InvoiceItem.period_end == current_cycle["period_end"],
        )
    )

def get_or_create_draft_invoice(db: Session, customer_id: str, run_date: date):
    invoice = db.scalar(
        select(Invoice).where(
            Invoice.status == "draft",
            Invoice.customer_id == customer_id,
        )
    )

    if not invoice:
        invoice = Invoice(
            invoice_number=generate_invoice_number(db, run_date),
            customer_id=customer_id,
            status="draft",
            due_date=run_date,
            subtotal=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            currency="USD",
        )
        db.add(invoice)
        db.flush()

    return invoice

def get_billing_periods(next_billing_date: date, billing_interval):
    period_end = next_billing_date
    period_start = period_end - billing_interval

    return {
        "period_start": period_start,
        "period_end": period_end,
    }

def build_invoice_item_values(subscription: Subscription, plan: Plan, item_type: str, excess_users: int = 0):
    if item_type == "subscription_base":
        return {
            "description": f"Subscription {subscription.id}",
            "quantity": 1,
            "unit_price": subscription.price,
            "amount": subscription.price,
        }

    if item_type == "usage_overage":
        unit_price = get_effective_overage_user_price(subscription, plan)
        quantity = excess_users
        amount = unit_price * quantity

        return {
            "description": f"Usage overage for subscription {subscription.id}",
            "quantity": quantity,
            "unit_price": unit_price,
            "amount": amount,
        }

    raise ValueError(f"Unsupported item type: {item_type}")

def calculate_excess_users(actual_usage: int, included_quota: int) -> int:
    return max(actual_usage - included_quota, 0)

def get_included_quota(subscription: Subscription, plan: Plan) -> int:
    if subscription.user_quota_override is not None and subscription.user_quota_override != 0:
        return subscription.user_quota_override
    return plan.user_quota

def get_effective_overage_user_price(subscription: Subscription, plan: Plan) -> Decimal:
    if subscription.overage_user_price_override is not None and subscription.overage_user_price_override != Decimal("0.00"):
        return subscription.overage_user_price_override
    return plan.overage_user_price

def get_invoice_period_key(run_date: date) -> str:
    return run_date.strftime("%Y%m")

def generate_invoice_number(db: Session, run_date: date) -> str:
    period_key = get_invoice_period_key(run_date)

    counter = db.scalar(
        select(InvoiceCounter)
        .where(InvoiceCounter.period_key == period_key)
        .with_for_update()
    )

    if not counter:
        counter = InvoiceCounter(period_key=period_key, last_value=0)
        db.add(counter)
        db.flush()

    counter.last_value += 1
    db.flush()

    invoice_number = f"INV-{period_key}-{counter.last_value:03d}"
    return invoice_number

def get_max_usage_for_period(db, subscription_id: str, current_cycle: dict) -> int:
    max_usage = db.scalar(
        select(func.max(UsageRecord.active_user_count)).where(
            UsageRecord.subscription_id == subscription_id,
            UsageRecord.recorded_on >= current_cycle["period_start"],
            UsageRecord.recorded_on < current_cycle["period_end"],
        )
    )

    return max_usage or 0
