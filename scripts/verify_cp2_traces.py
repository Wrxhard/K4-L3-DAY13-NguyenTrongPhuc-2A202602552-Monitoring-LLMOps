"""Verify CP2 observations and prompt labels without printing inputs or secrets."""

from __future__ import annotations

import json
import re
from pathlib import Path

from dotenv import load_dotenv
from langfuse import get_client


TRACE_IDS = [
    "c9aee46406dcec5ffbbf2e2aa23126ef",
    "2895c9bd9f7c9539c6b3b28ce4b0f70a",
    "90a9ff06d0aeaa385c027f118c1d674d",
    "2d0b7ca53d23d99c74aa274adcc31ad2",
    "c5bc7a14dba06963d6eb5027c9536798",
    "89ba907055749f61f7b4e7806f73c180",
    "1e8a216f6d8fd3fc87bb84c5e5425bc8",
    "86e4b236badf703e171bee3b5185981f",
    "cfa9f2536f5ae7975b37e477c67393b3",
    "b3a3831f3bfe558e2b5eb7ac62191ccc",
]
PROMPT_TRACES = {
    "baseline": ("3650ec0fb005867ce1ccb0ee49d446b2", 1),
    "candidate": ("3bd11d375b393b3f5fb18c943e7d4737", 2),
    "production-promoted": ("4902161ca7360eca6e9ef243dd537349", 2),
}
FIELDS = "core,basic,metadata,model,usage,prompt,io"


def observations(client, trace_id: str) -> list[dict]:
    result = client.api.observations.get_many(trace_id=trace_id, fields=FIELDS, limit=20)
    return [observation.model_dump() for observation in result.data]


def main() -> None:
    load_dotenv()
    client = get_client()
    log_path = Path(__file__).resolve().parents[1] / "data" / "logs.jsonl"
    log_ids = {
        record.get("correlation_id")
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if (record := json.loads(line)).get("event") == "response_sent"
    }
    print("CP2 Langfuse trace verification")
    for trace_id in TRACE_IDS:
        nodes = observations(client, trace_id)
        roots = [node for node in nodes if node.get("parent_observation_id") is None]
        assert len(roots) == 1, (trace_id, "root count")
        root = roots[0]
        children = [node for node in nodes if node.get("parent_observation_id") == root["id"]]
        assert {node["name"] for node in children} == {"retrieval", "fake-llm"}, trace_id
        generation = next(node for node in children if node["name"] == "fake-llm")
        retrieval = next(node for node in children if node["name"] == "retrieval")
        metadata = root.get("metadata") or {}
        assert root.get("type") == "AGENT" and retrieval.get("type") == "RETRIEVER"
        assert generation.get("type") == "GENERATION"
        assert re.fullmatch(r"[0-9a-f]{12}", root.get("user_id") or ""), trace_id
        assert root.get("session_id") and root.get("environment") == "dev", trace_id
        assert metadata.get("feature") and metadata.get("model") == "claude-sonnet-4-5", trace_id
        assert re.fullmatch(r"req-[0-9a-f]{8}", metadata.get("correlation_id") or ""), trace_id
        assert metadata["correlation_id"] in log_ids, trace_id
        assert generation.get("model") == "claude-sonnet-4-5", trace_id
        assert generation.get("prompt_name") == "day13-chat" and generation.get("prompt_version") == 1
        assert (generation.get("usage_details") or {}).get("input", 0) > 0
        assert (generation.get("usage_details") or {}).get("output", 0) > 0
        assert (generation.get("cost_details") or {}).get("total", 0) > 0
        assert generation.get("input") is None and generation.get("output") is None, trace_id
        assert root.get("input") is None and root.get("output") is None, trace_id
        print(f"{trace_id}: root={root['id']}, children=retrieval+fake-llm, correlation_id={metadata['correlation_id']}, log=matched, raw_io=none")

    for label, (trace_id, expected_version) in PROMPT_TRACES.items():
        nodes = observations(client, trace_id)
        root = next(node for node in nodes if node.get("parent_observation_id") is None)
        generation = next(node for node in nodes if node.get("name") == "fake-llm")
        metadata = root.get("metadata") or {}
        generation_metadata = generation.get("metadata") or {}
        assert metadata.get("prompt_name") == "day13-chat", label
        assert metadata.get("prompt_version") == expected_version, label
        assert generation_metadata.get("prompt_version") == expected_version, label
        assert generation.get("prompt_name") == "day13-chat" and generation.get("prompt_version") == expected_version
        assert metadata.get("prompt_source") == "langfuse", label
        assert metadata.get("prompt_label") == ("production" if label == "production-promoted" else label)
        assert generation.get("input") is None and generation.get("output") is None
        print(f"{label}: trace={trace_id}, prompt=day13-chat v{expected_version}, source=langfuse, raw_io=none")

    v1 = client.api.prompts.get("day13-chat", version=1)
    v2 = client.api.prompts.get("day13-chat", version=2)
    production = client.api.prompts.get("day13-chat", label="production")
    assert production.version == 1
    assert "baseline" in v1.labels and "production" in v1.labels
    assert "candidate" in v2.labels
    print(f"after rollback: v1={sorted(v1.labels)}, v2={sorted(v2.labels)}, production=v{production.version}")
    print("PASS: 10 child trees, 3 prompt traces, production rollback")


if __name__ == "__main__":
    main()
