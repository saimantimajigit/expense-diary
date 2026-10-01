from fastapi.testclient import TestClient


def _create(client: TestClient, *, amount: str, kind: str, time: str, category_id: int = 1) -> None:
    response = client.post(
        "/api/v1/transactions",
        json={
            "amount": amount,
            "transaction_type": kind,
            "merchant": "Cafe",
            "category_id": category_id,
            "transaction_time": time,
        },
    )
    assert response.status_code == 201


def test_dashboard_summary_calculates_period_totals_and_breakdown(client: TestClient) -> None:
    _create(client, amount="100.00", kind="expense", time="2026-10-01T09:00:00+05:30")
    _create(client, amount="50.00", kind="expense", time="2026-10-02T09:00:00+05:30")
    _create(client, amount="30.00", kind="income", time="2026-10-02T10:00:00+05:30", category_id=2)
    _create(client, amount="10.00", kind="refund", time="2026-10-03T10:00:00+05:30", category_id=2)

    response = client.get(
        "/api/v1/dashboard/summary?start_date=2026-10-01T00:00:00%2B05:30&end_date=2026-10-04T00:00:00%2B05:30"
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total_expense"] == "150.00"
    assert result["total_income"] == "30.00"
    assert result["total_refund"] == "10.00"
    assert result["transaction_count"] == 4
    assert result["average_daily_spend"] == "50.00"
    assert result["category_breakdown"] == [{"category": "Food", "amount": "150.00", "percentage": "100.00"}]
    assert len(result["recent_transactions"]) == 4


def test_monthly_dashboard_returns_month_totals(client: TestClient) -> None:
    _create(client, amount="31420.00", kind="expense", time="2026-10-01T09:00:00+05:30")

    response = client.get("/api/v1/dashboard/monthly?month=2026-10")

    assert response.status_code == 200
    assert response.json() == {
        "month": "2026-10",
        "total_spent": "31420.00",
        "categories": [{"category": "Food", "amount": "31420.00", "percentage": "100.00"}],
    }


def test_summary_rejects_mixed_month_and_date_range(client: TestClient) -> None:
    response = client.get(
        "/api/v1/dashboard/summary?month=2026-10&start_date=2026-10-01T00:00:00%2B05:30"
    )

    assert response.status_code == 422
