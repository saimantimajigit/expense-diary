from fastapi.testclient import TestClient


def test_create_transaction(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transactions",
        json={
            "amount": "420.00",
            "merchant": "  Cafe Green  ",
            "description": "Lunch",
            "category_id": 1,
            "payment_app": "gpay",
            "transaction_time": "2026-10-01T12:15:00+05:30",
        },
    )

    assert response.status_code == 201
    transaction = response.json()
    assert transaction["amount"] == "420.00"
    assert transaction["merchant"] == "Cafe Green"
    assert transaction["category"]["slug"] == "food"
    assert "raw_notification" not in transaction


def test_list_transactions_with_filters_and_pagination(client: TestClient) -> None:
    for merchant, amount in [("Cafe Green", "420.00"), ("Metro", "60.00")]:
        response = client.post(
            "/api/v1/transactions",
            json={
                "amount": amount,
                "merchant": merchant,
                "category_id": 1,
                "payment_app": "gpay",
                "transaction_time": "2026-10-01T12:15:00+05:30",
            },
        )
        assert response.status_code == 201

    response = client.get("/api/v1/transactions?merchant=cafe&category=food&limit=1")

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 1
    assert result["limit"] == 1
    assert result["items"][0]["merchant"] == "Cafe Green"


def test_update_and_delete_transaction(client: TestClient) -> None:
    created = client.post(
        "/api/v1/transactions",
        json={
            "amount": "120.50",
            "merchant": "Unknown Store",
            "transaction_time": "2026-10-01T12:15:00+05:30",
        },
    )
    transaction_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/transactions/{transaction_id}",
        json={"merchant": "  Local Store ", "category_id": 1},
    )
    deleted = client.delete(f"/api/v1/transactions/{transaction_id}")
    missing = client.get(f"/api/v1/transactions/{transaction_id}")

    assert updated.status_code == 200
    assert updated.json()["merchant"] == "Local Store"
    assert updated.json()["category"]["name"] == "Food"
    assert deleted.status_code == 204
    assert missing.status_code == 404




def test_transaction_can_be_uncategorized_and_duplicate_reference_conflicts(client: TestClient) -> None:
    payload = {
        "amount": "120.50",
        "merchant": "Unknown Store",
        "payment_app": "gpay",
        "transaction_reference": "manual-ref-1",
        "transaction_time": "2026-10-01T12:15:00+05:30",
    }
    created = client.post("/api/v1/transactions", json=payload)
    cleared = client.patch(f"/api/v1/transactions/{created.json()['id']}", json={"category_id": None})
    duplicate = client.post("/api/v1/transactions", json=payload)

    assert created.status_code == 201
    assert cleared.status_code == 200
    assert cleared.json()["category"] is None
    assert duplicate.status_code == 409
