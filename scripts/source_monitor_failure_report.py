"""Fail-closed, deduplicated GitHub issue reporting for source-watch failures.

This module never changes Registry source status, reviewed baselines, or releases.
It only renders an evidence link and a stable failure classification signature.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MARKER_PREFIX = "<!-- registry-source-monitor-failure-signature: "


def _ids(receipt: dict[str, Any], name: str) -> list[str]:
    value = receipt.get(name)
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise ValueError(f"invalid {name} in source-watch receipt")
    return sorted(set(value))


def failure_signature(receipt: dict[str, Any]) -> str:
    if receipt.get("overall_state") != "MONITOR_FAILURE":
        raise ValueError("failure reporting requires MONITOR_FAILURE receipt")
    failures = _ids(receipt, "failure_source_ids")
    if not failures:
        raise ValueError("MONITOR_FAILURE receipt has no failure sources")
    actionable = _ids(receipt, "actionable_source_ids")
    key = receipt.get("candidate_key")
    if key is not None and not isinstance(key, str):
        raise ValueError("invalid candidate_key in source-watch receipt")
    identity = {"failure_source_ids": failures, "actionable_source_ids": actionable,
                "candidate_key": key}
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def render_report(receipt: dict[str, Any], run_url: str) -> str:
    if not run_url.startswith("https://github.com/"):
        raise ValueError("expected a GitHub HTTPS workflow run URL")
    signature = failure_signature(receipt)
    failures = _ids(receipt, "failure_source_ids")
    actionable = _ids(receipt, "actionable_source_ids")
    candidate_key = receipt.get("candidate_key")
    receipt_location = (
        "Not generated; inspect the workflow logs"
        if failures == ["UNKNOWN"]
        else f"{run_url}#artifacts"
    )
    lines = [
        f"{MARKER_PREFIX}{signature} -->",
        "The scheduled official-source monitor could not complete a trustworthy check.",
        "",
        "**Unavailable sources:** " + ", ".join(f"`{x}`" for x in failures),
        "**Other sources requiring human review:** "
        + (", ".join(f"`{x}`" for x in actionable) if actionable else "None detected"),
        "**Candidate fingerprint:** " + (f"`{candidate_key}`" if candidate_key else "Not applicable"),
        f"**Workflow evidence:** {run_url}",
        f"**Receipt artifact:** {receipt_location}",
        "",
        "This remains a monitor failure. Changes detected for other sources are preserved in the receipt,",
        "but no automated candidate, source-status update, baseline acceptance, merge, or trusted release is authorized.",
        "Review official primary text and applicability before any Registry change.",
    ]
    return "\n".join(lines) + "\n"


def already_reported(previous_report: str, receipt: dict[str, Any]) -> bool:
    return f"{MARKER_PREFIX}{failure_signature(receipt)} -->" in previous_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--previous-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    previous = args.previous_report.read_text(encoding="utf-8")
    output = "" if already_reported(previous, receipt) else render_report(receipt, args.run_url)
    args.output.write_text(output, encoding="utf-8")
    print("SOURCE_MONITOR_FAILURE_REPORT=" + ("DEDUPLICATED" if not output else "NEW_SIGNATURE"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
