from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.plan import Plan
from sqlalchemy.orm import Session
from sqlalchemy import select
from collections import defaultdict

def group_due_subscriptions_by_customer(db: Session, run_date: date):
    grouped = defaultdict(list)

    due_subscriptions = db.scalars(
        select(Subscription).where(
            Subscription.status == "active",
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
                        continue

                    billing_interval = get_billing_interval(plan.interval)
                    period_end = subscription.next_billing_date
                    period_start = period_end - billing_interval

                    existing_item = get_existing_subscription_base_item(db, subscription.id, period_start, period_end)

                    if existing_item and subscription.next_billing_date <= run_date:
                        subscription.next_billing_date = subscription.next_billing_date + billing_interval

                    if not existing_item:
                        if invoice is None:
                            invoice = db.scalar(
                                select(Invoice).where(
                                    Invoice.status == "draft",
                                    Invoice.customer_id == customer_id,
                                )
                            )

                            if not invoice:
                                invoice = Invoice(
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

                        invoice_item = add_invoice_item(db, invoice, subscription, period_start, period_end)
                        recalculate_totals(db, invoice, invoice_item)

                        subscription.next_billing_date = subscription.next_billing_date + billing_interval
                
                db.commit()

            except Exception:
                db.rollback()
                raise

def add_invoice_item(db: Session, invoice: Invoice, subscription: Subscription, period_start: date, period_end: date):    
    invoice_item = InvoiceItem(
        invoice_id=invoice.id,
        subscription_id=subscription.id,
        item_type="subscription_base",
        description=f"Subscription {subscription.id}",
        period_start=period_start,
        period_end=period_end,
        quantity=1,
        unit_price=subscription.price,
        amount=1 * subscription.price
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
    period_start: date,
    period_end: date,
):
    return db.scalar(
        select(InvoiceItem).where(
            InvoiceItem.subscription_id == subscription_id,
            InvoiceItem.item_type == "subscription_base",
            InvoiceItem.period_start == period_start,
            InvoiceItem.period_end == period_end,
        )
    )

