from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CANONICAL_REPOSITORY = "Baelfyre/Orchestra-Compliance-Registry"
VERSION_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
SOURCE_STATES = {
    "VERIFIED_CURRENT",
    "CURRENT_WITH_PENDING_CHANGE",
    "NOT_EFFECTIVE_YET",
    "SUPERSEDED",
    "REPEALED",
    "SOURCE_UNAVAILABLE",
    "SOURCE_MOVED",
    "APPLICABILITY_UNRESOLVED",
    "HUMAN_INTERPRETATION_REQUIRED",
    "REVIEW_OVERDUE",
}
EXPECTED_RECORDS = {
    "sources": "registry/sources.json",
    "obligations": "registry/obligations.json",
    "jurisdictions": "registry/jurisdictions.json",
    "providers": "registry/providers.json",
    "source_status": "registry/source-status.json",
    "review_due": "registry/review-due.json",
}

SOURCE_WATCH_CANDIDATE_PATH = "machine/source-watch-candidate.json"
SOURCE_WATCH_RECEIPT_SCHEMA_VERSION = "orchestra.compliance-registry.source-watch-receipt.v1"
SOURCE_WATCH_RESULT_TO_LEDGER_STATUS = {
    "POTENTIAL_SUBSTANTIVE_CHANGE": "HUMAN_INTERPRETATION_REQUIRED",
    "SOURCE_MOVED": "SOURCE_MOVED",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def ids(items: list[dict[str, Any]], key: str, label: str) -> set[str]:
    seen: set[str] = set()
    for item in items:
        value = item.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} missing {key}")
        if value in seen:
            raise ValueError(f"duplicate {label}: {value}")
        seen.add(value)
    return seen


def string_list(value: Any, label: str, *, require_nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    if require_nonempty and not value:
        raise ValueError(f"{label} must not be empty")
    return value


def _coverage_error(label: str, expected: set[str], actual: set[str]) -> ValueError:
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    return ValueError(f"{label} coverage mismatch: missing={missing} extra={extra}")


def _source_watch_candidate_overrides(root: Path) -> dict[str, str]:
    path = root / SOURCE_WATCH_CANDIDATE_PATH
    if not path.is_file():
        raise ValueError(
            "source-watch candidate validation requires machine/source-watch-candidate.json"
        )

    receipt = load_json(path)
    if receipt.get("schema_version") != SOURCE_WATCH_RECEIPT_SCHEMA_VERSION:
        raise ValueError("source-watch candidate has unsupported schema_version")
    if receipt.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise ValueError("source-watch candidate canonical_repository mismatch")
    if receipt.get("overall_state") != "CHANGES_DETECTED":
        raise ValueError("source-watch candidate must record CHANGES_DETECTED")

    actionable_ids = receipt.get("actionable_source_ids")
    if (
        not isinstance(actionable_ids, list)
        or not actionable_ids
        or not all(isinstance(item, str) and item for item in actionable_ids)
        or len(actionable_ids) != len(set(actionable_ids))
    ):
        raise ValueError("source-watch candidate actionable_source_ids are malformed")

    failure_ids = receipt.get("failure_source_ids")
    if failure_ids != []:
        raise ValueError("source-watch change candidate must not contain monitor failures")

    source_results = receipt.get("source_results")
    if not isinstance(source_results, list) or not all(
        isinstance(item, dict) for item in source_results
    ):
        raise ValueError("source-watch candidate source_results are malformed")

    result_by_id: dict[str, dict[str, Any]] = {}
    for result in source_results:
        source_id = result.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("source-watch candidate result has invalid source_id")
        if source_id in result_by_id:
            raise ValueError(f"duplicate source-watch candidate result: {source_id}")
        result_by_id[source_id] = result

    derived_actionable = sorted(
        source_id
        for source_id, result in result_by_id.items()
        if result.get("state") in SOURCE_WATCH_RESULT_TO_LEDGER_STATUS
    )
    if sorted(actionable_ids) != derived_actionable:
        raise ValueError(
            "source-watch candidate actionable source set does not match source_results"
        )

    return {
        source_id: SOURCE_WATCH_RESULT_TO_LEDGER_STATUS[result_by_id[source_id]["state"]]
        for source_id in actionable_ids
    }


def validate(
    root: Path,
    *,
    today: date | None = None,
    allow_source_watch_candidate: bool = False,
) -> list[str]:
    try:
        today = today or date.today()
        manifest = load_json(root / "registry" / "manifest.json")
        if manifest.get("schema_version") != 1:
            raise ValueError("unsupported manifest schema_version")
        if manifest.get("canonical_repository") != CANONICAL_REPOSITORY:
            raise ValueError("canonical_repository mismatch")
        version = manifest.get("registry_version")
        if not isinstance(version, str) or VERSION_TOKEN_RE.fullmatch(version) is None:
            raise ValueError("registry_version must be a safe version token")
        status = manifest.get("status")
        if status not in {"DRAFT", "TRUSTED_RELEASE"}:
            raise ValueError("unsupported manifest status")
        sequence = manifest.get("release_sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
            raise ValueError("release_sequence must be non-negative")
        if status == "TRUSTED_RELEASE" and sequence == 0:
            raise ValueError("trusted releases require positive release_sequence")
        if manifest.get("records") != EXPECTED_RECORDS:
            raise ValueError("manifest records map does not match canonical registry paths")

        sources = load_json(root / "registry" / "sources.json").get("sources", [])
        obligations = load_json(root / "registry" / "obligations.json").get("obligations", [])
        jurisdictions = load_json(root / "registry" / "jurisdictions.json").get("jurisdictions", [])
        providers = load_json(root / "registry" / "providers.json").get("providers", [])
        source_status = load_json(root / "registry" / "source-status.json").get("entries", [])
        review_due = load_json(root / "registry" / "review-due.json").get("entries", [])
        stores = {
            "sources": sources,
            "obligations": obligations,
            "jurisdictions": jurisdictions,
            "providers": providers,
            "source_status": source_status,
            "review_due": review_due,
        }
        for label, items in stores.items():
            if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
                raise ValueError(f"{label} must be a list of objects")

        source_ids = ids(sources, "source_id", "source")
        jurisdiction_ids = ids(jurisdictions, "jurisdiction_id", "jurisdiction")
        provider_ids = ids(providers, "provider_id", "provider")
        ids(obligations, "obligation_id", "obligation")

        source_verification_states: dict[str, str] = {}
        for source in sources:
            source_id = source["source_id"]
            url = source.get("canonical_url")
            parsed = urlparse(url) if isinstance(url, str) else None
            if parsed is None or parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(f"source {source_id} requires canonical HTTPS URL")
            source_jurisdictions = string_list(source.get("jurisdiction_ids"), f"source {source_id} jurisdiction_ids")
            string_list(source.get("domains"), f"source {source_id} domains")
            verification = source.get("verification")
            state = verification.get("status") if isinstance(verification, dict) else None
            if state not in SOURCE_STATES:
                raise ValueError(f"source {source_id} has unsupported verification status")
            source_verification_states[source_id] = state
            for value in source_jurisdictions:
                if value not in jurisdiction_ids:
                    raise ValueError(f"source {source_id} references unknown jurisdiction {value}")

        for obligation in obligations:
            obligation_id = obligation["obligation_id"]
            refs = string_list(obligation.get("source_ids"), f"obligation {obligation_id} source_ids", require_nonempty=True)
            obligation_jurisdictions = string_list(obligation.get("jurisdiction_ids"), f"obligation {obligation_id} jurisdiction_ids")
            obligation_providers = string_list(obligation.get("provider_ids", []), f"obligation {obligation_id} provider_ids")
            string_list(obligation.get("domains"), f"obligation {obligation_id} domains")
            string_list(obligation.get("required_evidence"), f"obligation {obligation_id} required_evidence")
            for value in refs:
                if value not in source_ids:
                    raise ValueError(f"obligation {obligation_id} references unknown source {value}")
            for value in obligation_jurisdictions:
                if value not in jurisdiction_ids:
                    raise ValueError(f"obligation {obligation_id} references unknown jurisdiction {value}")
            for value in obligation_providers:
                if value not in provider_ids:
                    raise ValueError(f"obligation {obligation_id} references unknown provider {value}")

        source_status_ids = ids(source_status, "source_id", "source-status entry")
        source_status_states: dict[str, str] = {}
        for entry in source_status:
            source_id = entry["source_id"]
            if source_id not in source_ids:
                raise ValueError(f"source-status entry references unknown source {source_id}")
            entry_status = entry.get("status")
            if entry_status not in SOURCE_STATES:
                raise ValueError(f"source-status entry {source_id} has unsupported status")
            source_status_states[source_id] = entry_status

        review_due_ids = ids(review_due, "source_id", "review-due entry")
        parsed_due_dates: dict[str, date] = {}
        for entry in review_due:
            source_id = entry["source_id"]
            if source_id not in source_ids:
                raise ValueError(f"review-due entry references unknown source {source_id}")
            value = entry.get("next_review_due")
            if not isinstance(value, str):
                raise ValueError(f"review-due entry {source_id} requires next_review_due")
            try:
                parsed_due_dates[source_id] = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"review-due entry {source_id} has invalid next_review_due") from exc

        if source_status_ids != source_ids:
            raise _coverage_error("source-status", source_ids, source_status_ids)
        if review_due_ids != source_ids:
            raise _coverage_error("review-due", source_ids, review_due_ids)

        candidate_overrides = (
            _source_watch_candidate_overrides(root)
            if allow_source_watch_candidate
            else {}
        )
        unknown_candidate_ids = sorted(set(candidate_overrides) - source_ids)
        if unknown_candidate_ids:
            raise ValueError(
                f"source-watch candidate references unknown sources: {unknown_candidate_ids}"
            )
        for source_id, candidate_status in candidate_overrides.items():
            if source_status_states[source_id] != candidate_status:
                raise ValueError(
                    f"source-watch candidate/status drift: source={source_id} "
                    f"candidate={candidate_status} ledger={source_status_states[source_id]}"
                )

        for source_id in sorted(source_ids):
            source_state = source_verification_states[source_id]
            ledger_state = source_status_states[source_id]
            if (
                source_state != ledger_state
                and candidate_overrides.get(source_id) != ledger_state
            ):
                raise ValueError(
                    f"source {source_id} verification/status drift: source={source_state} ledger={ledger_state}"
                )
            if parsed_due_dates[source_id] < today and ledger_state != "REVIEW_OVERDUE":
                raise ValueError(
                    f"source {source_id} review is overdue as of {today.isoformat()}; "
                    "refresh the source or set status REVIEW_OVERDUE"
                )

        counts = manifest.get("record_counts")
        expected = {
            "sources": len(sources),
            "obligations": len(obligations),
            "jurisdictions": len(jurisdictions),
            "providers": len(providers),
            "source_status": len(source_status),
            "review_due": len(review_due),
        }
        if counts != expected:
            raise ValueError(f"record_counts mismatch: expected {expected}")
        return []
    except ValueError as exc:
        return [str(exc)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--allow-source-watch-candidate",
        action="store_true",
        help=(
            "Permit only receipt-backed source-status divergence on a generated "
            "source-watch candidate branch."
        ),
    )
    args = parser.parse_args(argv)
    errors = validate(
        Path(args.root),
        allow_source_watch_candidate=args.allow_source_watch_candidate,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("REGISTRY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
