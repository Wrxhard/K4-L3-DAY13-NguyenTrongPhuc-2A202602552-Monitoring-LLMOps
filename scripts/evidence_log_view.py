"""Show a small, readable selection of scrubbed JSONL records for screenshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


LOG = Path(__file__).resolve().parents[1] / "data" / "logs.jsonl"
FIELDS = (
    "ts", "event", "correlation_id", "user_id_hash", "session_id", "feature",
    "model", "env", "latency_ms", "ttft_ms", "tokens_in", "tokens_out",
    "cost_usd", "quality_score", "tool_success", "error_type", "payload",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="Show events with this correlation ID")
    group.add_argument("--latest", action="store_true", help="Show latest request and response")
    group.add_argument("--slowest", action="store_true", help="Show slowest response")
    args = parser.parse_args()
    records = [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.id:
        selected = [record for record in records if record.get("correlation_id") == args.id]
    elif args.slowest:
        responses = [record for record in records if record.get("event") == "response_sent"]
        selected = [max(responses, key=lambda record: record.get("latency_ms") or 0)] if responses else []
    else:
        relevant = [record for record in records if record.get("event") in {"request_received", "response_sent", "request_failed"}]
        latest_id = relevant[-1].get("correlation_id") if relevant else None
        selected = [record for record in relevant if record.get("correlation_id") == latest_id]
    if not selected:
        raise SystemExit("No matching log event found")
    for record in selected:
        print(json.dumps({key: record[key] for key in FIELDS if key in record}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
