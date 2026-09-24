# billing-platform

[![CI](https://github.com/lanatsirulnikov/billing-platform/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/lanatsirulnikov/billing-platform/actions/workflows/ci.yml)

## Local setup

### Requirements

- Python 3.11
- MySQL 8
- Node.js 20.19+ or 22.12+

### 1. Create the local database

Open MySQL as an administrator:

```bash
mysql -u root -p
```

Create the development database and user:

```sql
CREATE DATABASE IF NOT EXISTS billing_platform;
CREATE USER IF NOT EXISTS 'billing_user'@'localhost'
  IDENTIFIED BY 'billing_password';
GRANT ALL PRIVILEGES ON billing_platform.* TO 'billing_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
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

## Invoice Generation Strategy

- invoices are auto-generated every day
- generation only considers subscriptions whose NextBillingDate <= now
- after billing a subscription base item, its NextBillingDate is advanced by the billing interval
- overage is tied to the same customer, the same subscription, and the previous billing period
- real usage-based billing will later come from a usage_records table
- invoice numbers should use INV-YYYYMM-001 style

For each customer:

1. check subscriptions with due_date in a window from today - n days to today
2. for each due subscription, add a subscription charge as an invoice item
3. after adding that charge, move the subscription due_date forward by its billing interval
4. check extra users for the last billing period
5. add overage items for that period
6. if there is already an existing invoice you want to keep unchanged, create a new invoice instead of modifying the old one
7. if multiple subscriptions are due for the same customer during the run, they can all go onto one invoice

For each due subscription:

1. find its previous billing period
2. calculate usage in that period
3. create overage item only for that subscription and that previous period
4. do not duplicate overage for the same subscription-period pair

For a cancelled subscription:

- do not create new base items for periods after cancellation
- do allow usage_overage for the last completed overage period if it has not already been billed

For paused subscription:

Pause effective next cycle:
paused means:
- no new billing cycles start while paused
- current cycle remains billed normally
- no future base items until resumed
(Pause effective immediately with proration implementation later)

## Billing Investigation Assistant

The investigation service is organized as a small read-only tool workflow: it fetches invoices, fetches invoice items, compares invoice totals, compares charge categories, and returns structured tool-call logs. The workflow is guarded by a maximum tool-call limit and includes a versioned prompt identifier.

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
      "result": "Found 1 invoice items"
    },
    {
      "name": "compare_charge_categories",
      "status": "success",
      "result": "Current base: 99.00, Previous base: 99.00, Current overage: 25.00, Previous overage: 0"
    }
  ],
  "prompt_version": "billing-investigation-v1"
}
```

Currently supported explanations:
- usage overage increased
- subscription base charges increased
- multiple charge categories increased in the same invoice
- invoice total did not increase
- missing invoice and wrong-customer validation errors

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

### Overdue subscriptions

A generation run currently processes one billing interval per due subscription. If a subscription is multiple periods overdue, repeated generation runs are required to fully catch up.

Future improvement: support full overdue catch-up in one run by generating invoice items for each missed billing period before advancing the subscription beyond the run date.

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