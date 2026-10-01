from fastapi.testclient import TestClient
from app.services.transaction_service import sanitize_raw_payload


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "amount": "420.00",
        "merchant": "ABC Restaurant",
        "payment_app": "gpay",
        "transaction_time": "2026-10-01T20:15:00+05:30",
        "raw_notification": "Paid to ABC Restaurant\u0000",
        "raw_payload": {"packageName": "com.google.pay", "text": "Paid", "privateField": "drop"},
    }
    payload.update(overrides)
    return payload


def test_ingest_deduplicates_by_transaction_reference(client: TestClient) -> None:
    first = client.post("/api/v1/transactions/ingest", json=_payload(transaction_reference="upi-ref-1"))
    retry = client.post(
        "/api/v1/transactions/ingest",
        json=_payload(transaction_reference="upi-ref-1", amount="999.00"),
    )

    assert first.status_code == 201
    assert first.json()["duplicate"] is False
    assert retry.status_code == 200
    assert retry.json()["duplicate"] is True
    assert retry.json()["transaction"]["id"] == first.json()["transaction"]["id"]
    assert retry.json()["transaction"]["amount"] == "420.00"


def test_ingest_fingerprint_deduplicates_retries_but_keeps_later_payment(client: TestClient) -> None:
    first = client.post("/api/v1/transactions/ingest", json=_payload(transaction_reference=None))
    retry = client.post("/api/v1/transactions/ingest", json=_payload(transaction_reference=None))
    later = client.post(
        "/api/v1/transactions/ingest",
        json=_payload(transaction_reference=None, transaction_time="2026-10-01T20:16:00+05:30"),
    )

    assert first.status_code == 201
    assert retry.status_code == 200
    assert retry.json()["duplicate"] is True
    assert later.status_code == 201
    assert later.json()["duplicate"] is False


def test_distinct_references_allow_same_amount_merchant_and_time(client: TestClient) -> None:
    first = client.post("/api/v1/transactions/ingest", json=_payload(transaction_reference="upi-ref-a"))
    second = client.post("/api/v1/transactions/ingest", json=_payload(transaction_reference="upi-ref-b"))

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["transaction"]["id"] != second.json()["transaction"]["id"]


def test_ingest_does_not_expose_raw_notification_fields(client: TestClient) -> None:
    response = client.post("/api/v1/transactions/ingest", json=_payload())
    transaction_id = response.json()["transaction"]["id"]
    stored = client.get(f"/api/v1/transactions/{transaction_id}").json()

    assert response.status_code == 201
    assert "raw_notification" not in stored
    assert "raw_payload" not in stored


def test_raw_payload_sanitizer_whitelists_and_limits_notification_fields() -> None:
    sanitized = sanitize_raw_payload(
        {
            "packageName": "com.google.pay\u0000",
            "text": "x" * 1200,
            "postTime": 1_798_853_700_000,
            "unexpected": "private data",
        }
    )

    assert sanitized == {
        "packageName": "com.google.pay",
        "text": "x" * 1000,
        "postTime": 1_798_853_700_000,
    }
