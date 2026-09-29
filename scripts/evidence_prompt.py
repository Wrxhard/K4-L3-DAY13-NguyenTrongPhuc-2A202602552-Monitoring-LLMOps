"""Replay safe prompt-label evidence in the personal Langfuse project."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent import LabAgent
from app.tracing import get_langfuse_client


class EvidenceAgent(LabAgent):
    trace_id: str | None = None

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        self.trace_id = get_langfuse_client().get_current_trace_id()
        return super()._heuristic_quality(question, answer, docs)


def show_status(client) -> None:
    v1 = client.api.prompts.get("day13-chat", version=1)
    v2 = client.api.prompts.get("day13-chat", version=2)
    production = client.api.prompts.get("day13-chat", label="production")
    print(f"day13-chat v1 labels: {', '.join(sorted(v1.labels))}")
    print(f"day13-chat v2 labels: {', '.join(sorted(v2.labels))}")
    print(f"production -> v{production.version}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["status", "run", "promote", "rollback"])
    parser.add_argument("--label", choices=["baseline", "candidate", "production"])
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    client = get_langfuse_client()

    if args.action == "run":
        if not args.label:
            parser.error("run requires --label")
        os.environ["LANGFUSE_PROMPT_NAME"] = "day13-chat"
        os.environ["LANGFUSE_PROMPT_LABEL"] = args.label
        agent = EvidenceAgent()
        agent.run(
            user_id="capture-user",
            feature="qa",
            session_id="capture-prompt",
            message="Explain the observability workflow",
            correlation_id="req-cafe0002",
        )
        client.flush()
        if not agent.trace_id:
            raise RuntimeError("No Langfuse trace ID; check .env and connectivity")
        prompt = client.api.prompts.get("day13-chat", label=args.label)
        print(f"same input | label={args.label} | prompt=day13-chat v{prompt.version}")
        print(f"trace_id={agent.trace_id}")
        return

    if args.action == "promote":
        client.update_prompt(name="day13-chat", version=2, new_labels=["candidate", "production"])
    elif args.action == "rollback":
        client.update_prompt(name="day13-chat", version=1, new_labels=["baseline", "production"])
    show_status(client)


if __name__ == "__main__":
    main()
