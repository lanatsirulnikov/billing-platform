# Billing Platform

[![CI](https://github.com/lanatsirulnikov/billing-platform/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/lanatsirulnikov/billing-platform/actions/workflows/ci.yml)

Billing Platform is a FastAPI and PostgreSQL backend for managing customers,
plans, subscriptions, usage-based charges, and billing-cycle invoice generation.
It includes an optional AI-assisted investigation workflow that explains invoice
changes using verified billing facts and read-only, inspectable tools.

The project focuses on backend billing rules, transactional safety, duplicate
charge prevention, automated testing, and deterministic behavior when AI is
disabled or unavailable.

## Implemented capabilities

- Customer, plan, subscription, usage-record, and invoice APIs
- Recurring subscription and usage-overage invoice items
- Duplicate charge protection by subscription, charge type, and billing period
- Transaction rollback when invoice generation fails
- PostgreSQL invoice-number allocation with row locking
- Read-only invoice investigation with structured tool-call results
- Optional OpenAI explanations with deterministic fallback
- Docker Compose, database migrations, automated tests, linting, and CI

## Architecture

```text
React client / API consumers
            |
            v
       FastAPI routes
            |
            v
        Service layer
       /             \
      v               v
Invoice generation   Billing investigation
      |               |        |
      |               |        +--> Optional OpenAI explanation
      |               |             with deterministic fallback
      |               |
      |               +--> Read-only investigation tools
      |                     and structured tool-call results
      v
   SQLAlchemy ORM
            |
            v
      PostgreSQL 16
```

FastAPI routes handle HTTP validation and responses. Business rules remain in
the service layer, while SQLAlchemy manages persistence and PostgreSQL provides
transactions, uniqueness constraints, and invoice-number locking.

## Local setup

### Requirements

- Python 3.11
- PostgreSQL 16
- Node.js 20.19+ or 22.12+

### 1. Create the local PostgreSQL database

Open PostgreSQL as an administrator:

```bash
psql postgres
```

Depending on your PostgreSQL installation, you may need:

```bash
psql -U postgres
```

Create the development user and database:

```sql
CREATE USER billing_user WITH PASSWORD 'billing_password';
CREATE DATABASE billing_platform OWNER billing_user;
\q
```

These credentials are for local development only.

### 2. Install the backend

From the repository root:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate the environment with
`.venv\Scripts\Activate.ps1`.

### 3. Apply database migrations

Run this command from `backend` with the virtual environment active:

```bash
alembic upgrade head
```

### 4. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

Open the API documentation at <http://127.0.0.1:8000/docs> or check
<http://127.0.0.1:8000/health>.

### 5. Start the frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Open <http://localhost:5173>.

### 6. Run the checks

Backend tests:

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
```

Frontend lint and production build:

```bash
cd frontend
npm run lint
npm run build
```

## Billing generation behavior

Invoice generation is invoked explicitly with a billing run date. The project
does not currently include a scheduler or background worker.

For each generation run, the service:

1. Selects billable subscriptions whose `next_billing_date` is due.
2. Groups due subscriptions by customer.
3. Creates or reuses one draft invoice for that customer.
4. Adds a base subscription item for each unbilled subscription period.
5. Calculates usage overage from `usage_records` for the same subscription and period.
6. Prevents duplicate base and overage items using the subscription, item type,
   period start, and period end.
7. Recalculates invoice totals and advances the subscription by one billing interval.
8. Commits all changes for the customer together or rolls them back on failure.

Invoice numbers use the `INV-YYYYMM-NNN` format. PostgreSQL row locking protects
updates to an existing monthly invoice-number counter.

### Subscription state rules

- Active subscriptions advance to their next billing period after processing.
- Paused and cancelled subscriptions finish the currently processed cycle and
  are then marked as no longer billable.
- Immediate proration is not currently implemented.
- An overdue subscription advances one interval per generation run.

## Billing Investigation Assistant

The investigation service is organized as a small read-only tool workflow: it fetches invoices, fetches invoice items, compares invoice totals, compares charge categories, and returns structured tool-call logs. The workflow is guarded by a maximum tool-call limit and includes a versioned prompt identifier.

### AI architecture

```text
Client
  |
  v
FastAPI investigation endpoint
  |
  v
Billing investigation service
  |
  +--> Read-only tools
  |      +--> Fetch invoices
  |      +--> Fetch invoice items
  |      +--> Compare totals
  |      +--> Compare charge categories
  |
  v
Verified billing facts
  |
  +--> OpenAI enabled and available --> AI explanation
  |
  +--> Disabled or failed -----------> Deterministic fallback
  |
  v
Structured response with facts, tool calls, and ai_used
```

The backend includes a read-only billing investigation endpoint for answering:

> Why did this customer's invoice increase this month?

It compares two invoices for the same customer and returns a short explanation plus the facts used to produce it. The endpoint does not modify invoices, subscriptions, plans, or usage records.

Endpoint:

```http
POST /billing-investigations/invoice-increase
```

Example request:

```json
{
  "customer_id": "customer-id",
  "previous_invoice_id": "previous-invoice-id",
  "current_invoice_id": "current-invoice-id"
}
```

Example response:

```json
{
  "summary": "Invoice increased by 25.00. Usage overage increased by 25.00.",
  "current_total": "124.00",
  "previous_total": "99.00",
  "difference": "25.00",
  "facts": [
    "Current invoice total: 124.00",
    "Previous invoice total: 99.00",
    "Difference: 25.00",
    "Current subscription base total: 99.00",
    "Previous subscription base total: 99.00",
    "Current usage overage total: 25.00",
    "Previous usage overage total: 0"
  ],
  "tool_calls": [
    {
      "name": "fetch_current_invoice",
      "status": "success",
      "result": "Found invoice INV-202606-001"
    },
    {
      "name": "fetch_previous_invoice",
      "status": "success",
      "result": "Found invoice INV-202605-001"
    },
    {
      "name": "compare_invoice_totals",
      "status": "success",
      "result": "Current total: 124.00, Previous total: 99.00, Difference: 25.00"
    },
    {
      "name": "fetch_current_invoice_items",
      "status": "success",
      "result": "Found 2 invoice items"
    },
    {
      "name": "fetch_previous_invoice_items",
      "status": "success",
      "result": "Found 1 invoice item"
    },
    {
      "name": "compare_charge_categories",
      "status": "success",
      "result": "Current base: 99.00, Previous base: 99.00, Current overage: 25.00, Previous overage: 0"
    }
  ],
  "ai_used": false,
  "prompt_version": "billing-investigation-v1"
}
```

Currently supported explanations:
- usage overage increased
- subscription base charges increased
- multiple charge categories increased in the same invoice
- invoice total did not increase
- missing invoice and wrong-customer validation errors

`ai_used` indicates how the summary was produced:

- `true`: OpenAI generated the explanation.
- `false`: The deterministic billing explanation was used because AI was disabled or unavailable.

### Demo data

Create reproducible demo invoices for the billing investigation assistant.

For Docker:

```bash
docker compose exec backend sh -c 'PYTHONPATH=/app python scripts/seed_billing_investigation_demo.py'
```

For local backend:

```bash
cd backend
PYTHONPATH=. python scripts/seed_billing_investigation_demo.py
```

Example seed output:

```text
Demo data created.
customer_id=<generated-customer-id>
previous_invoice_id=<generated-previous-invoice-id>
current_invoice_id=<generated-current-invoice-id>
```

Copy the generated values into the request:

```bash
curl -X POST http://localhost:8000/billing-investigations/invoice-increase \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "<generated-customer-id>",
    "previous_invoice_id": "<generated-previous-invoice-id>",
    "current_invoice_id": "<generated-current-invoice-id>"
  }'
```

Example deterministic fallback result:

```json
{
  "summary": "Invoice increased by 25.00. Usage overage increased by 25.00.",
  "current_total": "124.00",
  "previous_total": "99.00",
  "difference": "25.00",
  "ai_used": false,
  "prompt_version": "billing-investigation-v1"
}
```

### Evaluation cases

The investigation endpoint is tested against these expected behaviors:

| Case | Expected explanation |
| --- | --- |
| Usage overage increased | Explains the invoice increase using the difference between current and previous usage overage totals. |
| Subscription base charges increased | Explains the invoice increase using the difference between current and previous subscription base totals. |
| No invoice increase | Reports that the invoice total did not increase. |
| Missing invoice | Returns a `404` error with `One or both invoices not found`. |
| Invoices from different customers | Returns a `400` error with `Invoices must belong to the requested customer`. |

### Override values

For subscription-level quota and overage price overrides:

- `None` means use the plan value.
- `0` / `0.00` also means use the plan value.
- Positive values override the plan value.

This keeps accidental zero values from creating unrealistic billing behavior, such as zero included users or free overage.

### Optional AI mode

The billing investigation endpoint uses deterministic explanations by default:

```env
BILLING_AI_ENABLED=false
```

To enable OpenAI-generated customer-facing explanations:

```env
BILLING_AI_ENABLED=true
OPENAI_API_KEY=your_api_key_here
BILLING_AI_MODEL=gpt-4.1-mini
```

If OpenAI is unavailable or the request fails, the endpoint returns the
deterministic explanation instead and reports `ai_used: false`.

## Engineering decisions

### Monetary values

Application calculations use Python `Decimal`, while database amounts use
fixed-precision `NUMERIC(10, 2)` columns. This avoids binary floating-point
rounding errors in invoice totals and usage charges.

### Transaction boundaries

Invoice generation commits once per customer. Invoice items, recalculated
totals, subscription billing dates, and billable-state changes are committed
together. If processing for that customer fails, the transaction is rolled back
and the error is propagated.

### Duplicate-charge prevention

Before adding an item, the service checks for an existing charge for the same
subscription, item type, and billing period. A database uniqueness constraint on
those fields provides an additional protection against duplicate base and
overage charges.

### Invoice-number allocation

Invoice numbers use a monthly counter and the `INV-YYYYMM-NNN` format.
PostgreSQL row locking serializes updates to an existing counter, and invoice
numbers also have a database uniqueness constraint.

### AI boundaries and fallback

Billing calculations remain in deterministic application code. The optional AI
layer receives verified facts and read-only tool results only. If AI is disabled
or unavailable, the endpoint returns a deterministic explanation and reports
`ai_used: false`.

### Failure behavior

Billing errors roll back the current customer transaction instead of leaving
partial invoice items or advanced billing dates. External AI failures are logged
and handled through the deterministic fallback rather than failing the billing
investigation request.

## Known limitations

- The API does not yet implement authentication, authorization, or enforced
  tenant isolation.
- Invoice generation is invoked synchronously and does not include a scheduler,
  queue, automatic retries, or job-status tracking.
- An overdue subscription advances one interval per generation run rather than
  generating all missed periods in one run.
- Paused and cancelled subscriptions do not support immediate proration.
- Concurrent billing execution has not yet been verified with a dedicated
  PostgreSQL concurrency test.
- Automatically generated invoices currently use USD and do not calculate tax
  or perform currency conversion.
- AI investigation tool calls are returned in the API response but are not
  persisted as a permanent audit record.
- The frontend is intentionally limited; the project primarily demonstrates
  backend design and billing behavior.

## Roadmap

- Add authentication, authorization, and customer-scoped data access.
- Run billing generation through a scheduler, queue, and background worker.
- Add PostgreSQL concurrency tests for duplicate charges and invoice numbers.
- Support full overdue-period catch-up in one billing run.
- Add proration rules for subscription pauses, cancellations, and plan changes.
- Define immutable finalized invoices and persistent billing audit history.
- Persist AI investigation runs and their tool-call outcomes.

## Docker setup

From the repository root:

```bash
cp .env.example .env
docker compose up --build
```

In another terminal, apply database migrations:

```bash
docker compose exec backend alembic upgrade head
```

Run backend tests inside the container:

```bash
docker compose exec backend pytest -q
```

Check the API health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```