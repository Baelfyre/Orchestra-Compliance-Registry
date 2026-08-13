from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CANONICAL_REPOSITORY = "Baelfyre/Orchestra-Compliance-Registry"
SOURCE_STATES = {
    "VERIFIED_CURRENT", "CURRENT_WITH_PENDING_CHANGE", "NOT_EFFECTIVE_YET",
    "SUPERSEDED", "REPEALED", "SOURCE_UNAVAILABLE", "SOURCE_MOVED",
    "APPLICABILITY_UNRESOLVED", "HUMAN_INTERPRETATION_REQUIRED", "REVIEW_OVERDUE",
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


def validate(root: Path) -> list[str]:
    try:
        manifest = load_json(root / "registry" / "manifest.json")
        if manifest.get("schema_version") != 1:
            raise ValueError("unsupported manifest schema_version")
        if manifest.get("canonical_repository") != CANONICAL_REPOSITORY:
            raise ValueError("canonical_repository mismatch")
        if manifest.get("status") not in {"DRAFT", "TRUSTED_RELEASE"}:
            raise ValueError("unsupported manifest status")
        sequence = manifest.get("release_sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
            raise ValueError("release_sequence must be non-negative")
        if manifest.get("status") == "TRUSTED_RELEASE" and sequence == 0:
            raise ValueError("trusted releases require positive release_sequence")

        sources = load_json(root / "registry" / "sources.json").get("sources", [])
        obligations = load_json(root / "registry" / "obligations.json").get("obligations", [])
        jurisdictions = load_json(root / "registry" / "jurisdictions.json").get("jurisdictions", [])
        providers = load_json(root / "registry" / "providers.json").get("providers", [])
        source_status = load_json(root / "registry" / "source-status.json").get("entries", [])
        review_due = load_json(root / "registry" / "review-due.json").get("entries", [])
        for label, items in {"sources": sources, "obligations": obligations, "jurisdictions": jurisdictions, "providers": providers, "source_status": source_status, "review_due": review_due}.items():
            if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
                raise ValueError(f"{label} must be a list of objects")

        source_ids = ids(sources, "source_id", "source")
        jurisdiction_ids = ids(jurisdictions, "jurisdiction_id", "jurisdiction")
        provider_ids = ids(providers, "provider_id", "provider")
        ids(obligations, "obligation_id", "obligation")

        for source in sources:
            source_id = source["source_id"]
            url = source.get("canonical_url")
            if not isinstance(url, str) or urlparse(url).scheme != "https" or not urlparse(url).netloc:
                raise ValueError(f"source {source_id} requires canonical HTTPS URL")
            state = source.get("verification", {}).get("status") if isinstance(source.get("verification"), dict) else None
            if state not in SOURCE_STATES:
                raise ValueError(f"source {source_id} has unsupported verification status")
            for value in source.get("jurisdiction_ids", []):
                if value not in jurisdiction_ids:
                    raise ValueError(f"source {source_id} references unknown jurisdiction {value}")

        for obligation in obligations:
            obligation_id = obligation["obligation_id"]
            refs = obligation.get("source_ids")
            if not isinstance(refs, list) or not refs:
                raise ValueError(f"obligation {obligation_id} requires source_ids")
            for value in refs:
                if value not in source_ids:
                    raise ValueError(f"obligation {obligation_id} references unknown source {value}")
            for value in obligation.get("jurisdiction_ids", []):
                if value not in jurisdiction_ids:
                    raise ValueError(f"obligation {obligation_id} references unknown jurisdiction {value}")
            for value in obligation.get("provider_ids", []):
                if value not in provider_ids:
                    raise ValueError(f"obligation {obligation_id} references unknown provider {value}")

        counts = manifest.get("record_counts")
        expected = {"sources": len(sources), "obligations": len(obligations), "jurisdictions": len(jurisdictions), "providers": len(providers), "source_status": len(source_status), "review_due": len(review_due)}
        if counts != expected:
            raise ValueError(f"record_counts mismatch: expected {expected}")
        return []
    except ValueError as exc:
        return [str(exc)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args(argv)
    errors = validate(Path(args.root))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("REGISTRY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
