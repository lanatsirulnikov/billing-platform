from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal

from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.schemas.billing_investigation import InvoiceIncreaseIn, InvoiceIncreaseOut

MAX_TOOL_CALLS = 6

PROMPT_VERSION = "billing-investigation-v1"

BILLING_INVESTIGATION_PROMPT = """
You are a read-only billing investigation assistant.
Explain why a customer's invoice changed by comparing invoices, invoice items,
subscriptions, plans, and usage records.
Use only retrieved billing records.
Do not modify billing data.
Return a concise summary and the facts used.
""".strip()


class InvoiceInvestigationNotFound(Exception):
    pass


class InvoiceInvestigationInvalidInput(Exception):
    pass


def investigate_invoice_increase(db: Session, input: InvoiceIncreaseIn) -> InvoiceIncreaseOut:
    tool_calls = []

    invoices = db.scalars(
        select(Invoice).where(
            Invoice.id.in_([input.current_invoice_id, input.previous_invoice_id])
        )
    ).all()

    current_invoice = fetch_invoice(
        invoices,
        input.current_invoice_id,
        tool_calls,
        tool_name="fetch_current_invoice",
        missing_result="Current invoice not found",
    )

    previous_invoice = fetch_invoice(
        invoices,
        input.previous_invoice_id,
        tool_calls,
        tool_name="fetch_previous_invoice",
        missing_result="Previous invoice not found",
    )

    if not current_invoice or not previous_invoice:
        raise InvoiceInvestigationNotFound("One or both invoices not found")

    if (current_invoice.customer_id != input.customer_id
        or previous_invoice.customer_id != input.customer_id
    ):
        raise InvoiceInvestigationInvalidInput(
            "Invoices must belong to the requested customer"
        )

    current_total = current_invoice.total_amount
    previous_total = previous_invoice.total_amount
    difference = compare_invoice_totals(
        current_total=current_total,
        previous_total=previous_total,
        tool_calls=tool_calls,
        tool_name="compare_invoice_totals",
    )

    current_items = fetch_invoice_items(
        db,
        current_invoice.id,
        tool_calls,
        tool_name="fetch_current_invoice_items",
        missing_result="Current invoice items not found",
    )
    
    previous_items = fetch_invoice_items(
        db,
        previous_invoice.id,
        tool_calls,
        tool_name="fetch_previous_invoice_items",
        missing_result="Previous invoice items not found",
    )

    current_overage = sum(item.amount for item in current_items if item.item_type == "usage_overage")
    previous_overage = sum(item.amount for item in previous_items if item.item_type == "usage_overage")
    current_base = sum(item.amount for item in current_items if item.item_type == "subscription_base")
    previous_base = sum(item.amount for item in previous_items if item.item_type == "subscription_base")

    facts = [
        f"Current invoice total: {current_total}",
        f"Previous invoice total: {previous_total}",
    ]

    summary = compare_charge_categories(
        current_base=current_base,
        previous_base=previous_base,
        current_overage=current_overage,
        previous_overage=previous_overage,
        tool_calls=tool_calls,
        tool_name="compare_charge_categories",
        difference=difference,
        facts=facts,
    )

    return InvoiceIncreaseOut(
        summary=summary,
        current_total=current_total,
        previous_total=previous_total,
        difference=difference,
        facts=facts,
        tool_calls=tool_calls,
        prompt_version=PROMPT_VERSION,
    )

def record_tool_call(tool_calls: list[dict], name: str, status: str, result: str) -> None:
    if len(tool_calls) >= MAX_TOOL_CALLS:
        raise InvoiceInvestigationInvalidInput("Maximum tool calls exceeded")

    tool_calls.append({
        "name": name,
        "status": status,
        "result": result,
    })

def fetch_invoice(   
    invoices: list[Invoice],
    invoice_id: str,
    tool_calls: list[dict],
    tool_name: str,
    missing_result: str,
) -> Invoice | None:
    invoice = next((inv for inv in invoices if inv.id == invoice_id), None)

    record_tool_call(
        tool_calls,
        name=tool_name,
        status="success" if invoice else "failed",
        result=(
            f"Found invoice {invoice.invoice_number}"
            if invoice
            else missing_result
        )
    )
    return invoice

def fetch_invoice_items(
    db: Session,
    invoice_id: str,
    tool_calls: list[dict],
    tool_name: str,
    missing_result: str,
) -> list[InvoiceItem]:
    items = db.scalars(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id)
    ).all()

    record_tool_call(
        tool_calls,
        name=tool_name,
        status="success" if items else "failed",
        result=f"Found {len(items)} invoice item{'s' if len(items) != 1 else ''}"
    )
    return items

def compare_invoice_totals(
    current_total: Decimal,
    previous_total: Decimal,
    tool_calls: list[dict],
    tool_name: str,
) -> Decimal:
    difference = current_total - previous_total

    record_tool_call(
        tool_calls,
        name=tool_name,
        status="success",
        result=f"Current total: {current_total}, Previous total: {previous_total}, Difference: {difference}"
    )

    return difference

def compare_charge_categories(
    current_base: Decimal,
    previous_base: Decimal,
    current_overage: Decimal,
    previous_overage: Decimal,
    tool_calls: list[dict],
    tool_name: str,
    difference: Decimal,
    facts: list[str],
) -> str:
    for fact in [
        f"Difference: {difference}",
        f"Current subscription base total: {current_base}",
        f"Previous subscription base total: {previous_base}",
        f"Current usage overage total: {current_overage}",
        f"Previous usage overage total: {previous_overage}",
    ]:
        facts.append(fact)


    # TODO: Support multi-factor explanations when several charge categories increase in the same invoice.
    # For now, the summary reports the strongest single reason handled by this service.
    if difference == 0:
        summary = "Invoice total did not increase."
    elif difference < 0:
        summary = f"Invoice total decreased by {abs(difference)}."
    else:
        summary = f"Invoice total changed by {difference}."

    if current_base > previous_base:
        summary = (
            f"Invoice increased by {difference}. "
            f"Subscription base charges increased by {current_base - previous_base}."
        )

    if current_overage > previous_overage:
        summary = (
            f"Invoice increased by {difference}. "
            f"Usage overage increased by {current_overage - previous_overage}."
        )

    record_tool_call(
        tool_calls,
        name=tool_name,
        status="success",
        result=f"Current base: {current_base}, Previous base: {previous_base}, Current overage: {current_overage}, Previous overage: {previous_overage}"
    )
    return summary