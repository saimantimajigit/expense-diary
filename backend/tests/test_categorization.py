from fastapi.testclient import TestClient

from app.services.merchant_normalization import normalize_merchant


def test_merchant_normalization() -> None:
    assert normalize_merchant("SWIGGY LIMITED") == "swiggy"
    assert normalize_merchant("Swiggy") == "swiggy"
    assert normalize_merchant("Swiggy Payments") == "swiggy"


def test_categorizes_known_merchant_and_falls_back(client: TestClient) -> None:
    known = client.post(
        "/api/v1/transactions",
        json={"amount": "75.00", "merchant": "SWIGGY LIMITED", "transaction_time": "2026-10-01T12:00:00+05:30"},
    )
    unknown = client.post(
        "/api/v1/transactions",
        json={"amount": "25.00", "merchant": "Corner shop", "transaction_time": "2026-10-01T12:01:00+05:30"},
    )

    assert known.status_code == 201
    assert known.json()["category"]["slug"] == "food"
    assert unknown.status_code == 201
    assert unknown.json()["category"]["slug"] == "other"


def test_explicit_category_overrides_merchant_rule(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transactions",
        json={
            "amount": "75.00",
            "merchant": "Swiggy",
            "category_id": 2,
            "transaction_time": "2026-10-01T12:00:00+05:30",
        },
    )

    assert response.status_code == 201
    assert response.json()["category"]["slug"] == "other"
