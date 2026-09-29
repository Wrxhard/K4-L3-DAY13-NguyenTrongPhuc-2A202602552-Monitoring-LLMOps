from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any


def load_log_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _percentile(values: list[float], percent: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(len(ordered) * percent / 100) - 1)], 2)


def _number(record: dict[str, Any], key: str) -> float | None:
    value = record.get(key)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def build_dashboard_snapshot(
    records: list[dict[str, Any]], config: dict[str, Any], now: datetime
) -> dict[str, Any]:
    dashboard = config["dashboard"]
    minutes = dashboard["time_range_minutes"]
    now = now.astimezone(timezone.utc)
    start = now - timedelta(minutes=minutes)
    first_bucket = now.replace(second=0, microsecond=0) - timedelta(minutes=minutes - 1)
    times = [first_bucket + timedelta(minutes=i) for i in range(minutes)]
    buckets: dict[datetime, list[dict[str, Any]]] = defaultdict(list)
    current: list[dict[str, Any]] = []
    for record in records:
        try:
            timestamp = datetime.fromisoformat(str(record["ts"]).replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            timestamp = timestamp.astimezone(timezone.utc)
        except (KeyError, TypeError, ValueError):
            continue
        if start <= timestamp <= now:
            current.append(record)
            buckets[timestamp.replace(second=0, microsecond=0)].append(record)

    def by_event(items: list[dict[str, Any]], event: str) -> list[dict[str, Any]]:
        return [item for item in items if item.get("event") == event]

    def values(items: list[dict[str, Any]], key: str) -> list[float]:
        return [number for item in items if (number := _number(item, key)) is not None]

    def ratio(numerator: int, denominator: int) -> float | None:
        return round(numerator / denominator * 100, 2) if denominator else None

    requests = by_event(current, "request_received")
    responses = by_event(current, "response_sent")
    failures = by_event(current, "request_failed")
    tool_events = [item for item in current if isinstance(item.get("tool_success"), bool)]
    panel_metrics = {
        "latency": {
            "p50": _percentile(values(responses, "latency_ms"), 50),
            "p95": _percentile(values(responses, "latency_ms"), 95),
            "p99": _percentile(values(responses, "latency_ms"), 99),
            "ttft_p95": _percentile(values(responses, "ttft_ms"), 95),
        },
        "traffic": {"count": len(requests), "rate_per_minute": round(len(requests) / minutes, 2)},
        "errors": {
            "error_rate_pct": ratio(len(failures), len(requests)),
            "breakdown": dict(Counter(item.get("error_type") or "unknown" for item in failures)),
            "retrieval_success_pct": ratio(sum(item["tool_success"] for item in tool_events), len(tool_events)),
        },
        "cost": {"total": round(sum(values(responses, "cost_usd")), 6)},
        "tokens": {
            "input": int(sum(values(responses, "tokens_in"))),
            "output": int(sum(values(responses, "tokens_out"))),
        },
        "quality": {"mean": round(mean(values(responses, "quality_score")), 2) if values(responses, "quality_score") else None},
    }

    per_minute = []
    running_cost = running_input = running_output = 0
    for minute in times:
        items = buckets[minute]
        req = by_event(items, "request_received")
        resp = by_event(items, "response_sent")
        fail = by_event(items, "request_failed")
        tool = [item for item in items if isinstance(item.get("tool_success"), bool)]
        running_cost += sum(values(resp, "cost_usd"))
        running_input += int(sum(values(resp, "tokens_in")))
        running_output += int(sum(values(resp, "tokens_out")))
        quality_values = values(resp, "quality_score")
        per_minute.append({
            "p50": _percentile(values(resp, "latency_ms"), 50),
            "p95": _percentile(values(resp, "latency_ms"), 95),
            "p99": _percentile(values(resp, "latency_ms"), 99),
            "ttft_p95": _percentile(values(resp, "ttft_ms"), 95),
            "requests": len(req),
            "error_rate_pct": ratio(len(fail), len(req)),
            "retrieval_success_pct": ratio(sum(item["tool_success"] for item in tool), len(tool)),
            "cost_cumulative": round(running_cost, 6),
            "tokens_input_cumulative": running_input,
            "tokens_output_cumulative": running_output,
            "tokens_total_cumulative": running_input + running_output,
            "quality_mean": round(mean(quality_values), 2) if quality_values else None,
        })

    chart_fields = {
        "latency": (("P50", "p50"), ("P95", "p95"), ("P99", "p99"), ("TTFT P95", "ttft_p95")),
        "traffic": (("Requests/min", "requests"),),
        "errors": (("Error rate", "error_rate_pct"), ("Retrieval success", "retrieval_success_pct")),
        "cost": (("Cumulative cost", "cost_cumulative"),),
        "tokens": (("Input", "tokens_input_cumulative"), ("Output", "tokens_output_cumulative"), ("Total", "tokens_total_cumulative")),
        "quality": (("Mean quality", "quality_mean"),),
    }
    panels = []
    for panel in dashboard["panels"]:
        panel_id = panel["id"]
        panels.append({
            "id": panel_id,
            "title": panel["title"],
            "unit": panel["unit"],
            "threshold": panel["threshold"],
            "metrics": panel_metrics[panel_id],
            "times": [minute.isoformat() for minute in times],
            "series": [
                {"name": name, "values": [point[field] for point in per_minute]}
                for name, field in chart_fields[panel_id]
            ],
        })
    return {
        "title": dashboard["title"],
        "generated_at": now.isoformat(),
        "time_range_minutes": minutes,
        "refresh_seconds": dashboard["refresh_seconds"],
        "source": "data/logs.jsonl",
        "panels": panels,
    }
