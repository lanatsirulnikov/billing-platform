
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.schemas.billing_investigation import InvoiceIncreaseIn, InvoiceIncreaseOut


class InvoiceInvestigationNotFound(Exception):
    pass


class InvoiceInvestigationInvalidInput(Exception):
    pass


def investigate_invoice_increase(db: Session, input: InvoiceIncreaseIn) -> InvoiceIncreaseOut:
    tool_calls = ["fetch_current_invoice", "fetch_previous_invoice"]

    invoices = db.scalars(
        select(Invoice).where(
            Invoice.id.in_([input.current_invoice_id, input.previous_invoice_id])
        )
    ).all()

    current_invoice = next((inv for inv in invoices if inv.id == input.current_invoice_id), None)
    previous_invoice = next((inv for inv in invoices if inv.id == input.previous_invoice_id), None)

    if not current_invoice or not previous_invoice:
        raise InvoiceInvestigationNotFound("One or both invoices not found")

    if current_invoice.customer_id != input.customer_id or previous_invoice.customer_id != input.customer_id:
        raise InvoiceInvestigationInvalidInput("Invoices must belong to the requested customer")

    current_total = current_invoice.total_amount
    previous_total = previous_invoice.total_amount
    difference = current_total - previous_total
    tool_calls.append("compare_invoice_totals")

    current_items = db.scalars(
        select(InvoiceItem).where(InvoiceItem.invoice_id == current_invoice.id)
    ).all()
    tool_calls.append("fetch_current_invoice_items")
    previous_items = db.scalars(
        select(InvoiceItem).where(InvoiceItem.invoice_id == previous_invoice.id)
    ).all()
    tool_calls.append("fetch_previous_invoice_items")

    current_overage = sum(item.amount for item in current_items if item.item_type == "usage_overage")
    previous_overage = sum(item.amount for item in previous_items if item.item_type == "usage_overage")
    current_base = sum(item.amount for item in current_items if item.item_type == "subscription_base")
    previous_base = sum(item.amount for item in previous_items if item.item_type == "subscription_base")

    facts = [
        f"Current invoice total: {current_total}",
        f"Previous invoice total: {previous_total}",
        f"Difference: {difference}",
        f"Current subscription base total: {current_base}",
        f"Previous subscription base total: {previous_base}",
        f"Current usage overage total: {current_overage}",
        f"Previous usage overage total: {previous_overage}",
    ]

    # TODO: Support multi-factor explanations when several charge categories increase in the same invoice.
    # For now, the summary reports the strongest single reason handled by this service.
    if difference == 0:
        summary = "Invoice total did not increase."
    elif difference < 0:
        summary = f"Invoice total decreased by {abs(difference)}."
    else:
        summary = f"Invoice total changed by {difference}."

    if current_base > previous_base:
        summary = f"Invoice increased by {difference}. Subscription base charges increased by {current_base - previous_base}."

    if current_overage > previous_overage:
        summary = f"Invoice increased by {difference}. Usage overage increased by {current_overage - previous_overage}."

    tool_calls.append("compare_charge_categories")


    return InvoiceIncreaseOut(
        summary=summary,
        current_total=current_total,
        previous_total=previous_total,
        difference=difference,
        facts=facts,
        tool_calls=tool_calls,
    )
