from fastapi.testclient import TestClient


def test_learning_merchant_rule_changes_future_categorization(client: TestClient) -> None:
    learned = client.post(
        "/api/v1/merchant-rules",
        json={"merchant_pattern": "SWIGGY Payments", "category_id": 2},
    )
    transaction = client.post(
        "/api/v1/transactions/ingest",
        json={
            "amount": "120.00",
            "merchant": "Swiggy Limited",
            "payment_app": "gpay",
            "transaction_time": "2026-10-01T12:15:00+05:30",
        },
    )

    assert learned.status_code == 201
    assert learned.json()["merchant_pattern"] == "swiggy"
    assert learned.json()["priority"] == 10
    assert transaction.status_code == 201
    assert transaction.json()["transaction"]["category"]["slug"] == "other"


def test_learning_same_pattern_updates_existing_rule(client: TestClient) -> None:
    first = client.post("/api/v1/merchant-rules", json={"merchant_pattern": "Uber", "category_id": 1})
    updated = client.post("/api/v1/merchant-rules", json={"merchant_pattern": "UBER Payments", "category_id": 2})
    rules = client.get("/api/v1/merchant-rules")

    assert first.status_code == 201
    assert updated.status_code == 201
    assert updated.json()["id"] == first.json()["id"]
    uber_rules = [rule for rule in rules.json() if rule["merchant_pattern"] == "uber"]
    assert len(uber_rules) == 1
    assert uber_rules[0]["category_id"] == 2
