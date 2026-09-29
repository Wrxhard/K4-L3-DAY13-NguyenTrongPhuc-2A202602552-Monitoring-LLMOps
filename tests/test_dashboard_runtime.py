from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from dashboard.metrics import build_dashboard_snapshot


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_aggregates_six_panels_from_one_60_minute_window() -> None:
    now = datetime(2026, 9, 29, 8, 30, tzinfo=timezone.utc)
    config = yaml.safe_load((REPO_ROOT / "config/dashboard.yaml").read_text(encoding="utf-8"))

    def record(event: str, minute_ago: int, **fields) -> dict:
        return {"ts": (now - timedelta(minutes=minute_ago)).isoformat(), "event": event, **fields}

    records = [
        record("request_received", 2),
        record("response_sent", 2, latency_ms=100, ttft_ms=30, cost_usd=0.01, tokens_in=10, tokens_out=20, quality_score=0.8, tool_success=True),
        record("request_received", 1),
        record("response_sent", 1, latency_ms=300, ttft_ms=50, cost_usd=0.02, tokens_in=30, tokens_out=40, quality_score=0.6, tool_success=True),
        record("request_received", 0),
        record("request_failed", 0, error_type="RuntimeError", tool_success=False),
        record("request_received", 61),
        record("request_failed", 61, error_type="OldError", tool_success=False),
    ]

    snapshot = build_dashboard_snapshot(records, config, now)
    panels = {panel["id"]: panel for panel in snapshot["panels"]}

    assert snapshot["time_range_minutes"] == 60
    assert snapshot["refresh_seconds"] == 30
    assert set(panels) == {"latency", "traffic", "errors", "cost", "tokens", "quality"}
    assert panels["latency"]["metrics"] == {"p50": 100, "p95": 300, "p99": 300, "ttft_p95": 50}
    assert panels["traffic"]["metrics"]["count"] == 3
    assert panels["errors"]["metrics"] == {
        "error_rate_pct": 33.33,
        "breakdown": {"RuntimeError": 1},
        "retrieval_success_pct": 66.67,
    }
    assert panels["cost"]["metrics"]["total"] == 0.03
    assert panels["tokens"]["metrics"] == {"input": 40, "output": 60}
    assert panels["quality"]["metrics"]["mean"] == 0.7
    assert all(len(series["values"]) == 60 for panel in panels.values() for series in panel["series"])
    assert all(panel["threshold"]["value"] == config["dashboard"]["panels"][i]["threshold"]["value"] for i, panel in enumerate(snapshot["panels"]))


def test_dashboard_returns_empty_counts_without_inventing_percentiles() -> None:
    now = datetime(2026, 9, 29, 8, 30, tzinfo=timezone.utc)
    config = yaml.safe_load((REPO_ROOT / "config/dashboard.yaml").read_text(encoding="utf-8"))
    snapshot = build_dashboard_snapshot([], config, now)
    panels = {panel["id"]: panel for panel in snapshot["panels"]}
    assert panels["traffic"]["metrics"]["count"] == 0
    assert panels["latency"]["metrics"]["p95"] is None
    assert panels["errors"]["metrics"]["error_rate_pct"] is None
    assert panels["quality"]["metrics"]["mean"] is None
