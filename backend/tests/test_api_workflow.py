def test_customer_plan_subscription_invoice_api_workflow(client):
    customer_response = client.post(
        "/customers",
        json={
            "name": "API Customer",
            "email": "api-customer@example.com",
        },
    )
    assert customer_response.status_code == 200
    customer = customer_response.json()

    plan_response = client.post(
        "/plans",
        json={
            "name": "API Monthly",
            "price": "99.00",
            "user_quota": 10,
            "overage_user_price": "5.00",
            "interval": "monthly",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()

    subscription_response = client.post(
        "/subscriptions",
        json={
            "customer_id": customer["id"],
            "plan_id": plan["id"],
            "price": "99.00",
            "user_quota_override": None,
            "overage_user_price_override": None,
            "status": "active",
            "start_date": "2026-05-01",
            "end_date": None,
            "next_billing_date": "2026-06-01",
            "is_billable": True,
        },
    )
    assert subscription_response.status_code == 200
    subscription = subscription_response.json()

    invoice_response = client.post(
        "/invoices/generate-due",
        params={"run_date": "2026-06-01"},
    )
    assert invoice_response.status_code == 200

    invoices_response = client.get("/invoices")
    assert invoices_response.status_code == 200
    invoices = invoices_response.json()

    assert len(invoices) == 1
    assert invoices[0]["customer_id"] == customer["id"]
    assert invoices[0]["subtotal"] == "99.00"
    assert invoices[0]["total_amount"] == "99.00"

    subscription_after_response = client.get(f"/subscriptions/{subscription['id']}")
    assert subscription_after_response.status_code == 200
    subscription_after = subscription_after_response.json()

    assert subscription_after["next_billing_date"] == "2026-07-01"
    assert subscription_after["is_billable"] is True