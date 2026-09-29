from __future__ import annotations

import json
import asyncio
import re
from pathlib import Path

import httpx

from app import logging_config
from app.main import app
from app.pii import hash_user_id


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post(
                "/chat",
                json={
                    "user_id": "student-01",
                    "session_id": "session-01",
                    "feature": "qa",
                    "message": "Explain observability",
                },
            )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert response_event["quality_score"] == response.json()["quality_score"]
    assert response_event["ttft_ms"] == response.json()["ttft_ms"]
    assert response_event["tool_name"] == "retrieval"
    assert response_event["tool_success"] is True


def test_request_id_headers_and_log_context_do_not_leak_between_requests(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    async def send_requests() -> tuple[httpx.Response, httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post(
                "/chat",
                headers={"x-request-id": "req-1234abcd"},
                json={"user_id": "user-a", "session_id": "session-a", "feature": "qa", "message": "First request"},
            )
            second = await client.post(
                "/chat",
                headers={"x-request-id": "not-a-valid-id"},
                json={"user_id": "user-b", "session_id": "session-b", "feature": "summary", "message": "Second request"},
            )
            return first, second

    first, second = asyncio.run(send_requests())
    assert first.status_code == second.status_code == 200
    assert first.headers["x-request-id"] == first.json()["correlation_id"] == "req-1234abcd"
    assert re.fullmatch(r"req-[0-9a-f]{8}", second.headers["x-request-id"])
    assert second.headers["x-request-id"] == second.json()["correlation_id"]
    assert second.headers["x-request-id"] != first.headers["x-request-id"]
    assert float(first.headers["x-response-time-ms"]) >= 0
    assert float(second.headers["x-response-time-ms"]) >= 0

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    received = [record for record in records if record["event"] == "request_received"]
    assert len(received) == 2
    for record, response, user_id, session_id, feature in (
        (received[0], first, "user-a", "session-a", "qa"),
        (received[1], second, "user-b", "session-b", "summary"),
    ):
        assert record["correlation_id"] == response.headers["x-request-id"]
        assert record["user_id_hash"] == hash_user_id(user_id)
        assert record["session_id"] == session_id
        assert record["feature"] == feature
        assert record["model"] == "claude-sonnet-4-5"
        assert record["env"] == "dev"


def test_log_writer_scrubs_nested_payload_and_context(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    log = logging_config.get_logger()
    log.info(
        "pii_probe",
        service="api",
        session_id="student@vinuni.edu.vn",
        payload={"nested": {"phone": "090 123 4567", "identifiers": ["001234567890", "4111-1111-1111-1111"]}},
    )
    raw = log_path.read_text(encoding="utf-8")
    for value in ("student@vinuni.edu.vn", "090 123 4567", "001234567890", "4111-1111-1111-1111"):
        assert value not in raw
    assert "REDACTED_EMAIL" in raw
    assert "REDACTED_PHONE_VN" in raw
    assert "REDACTED_CCCD" in raw
    assert "REDACTED_CREDIT_CARD" in raw
