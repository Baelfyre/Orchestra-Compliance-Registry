from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.validate_schema_contracts import validate_value
except ModuleNotFoundError:
    from validate_schema_contracts import validate_value

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_REPOSITORY = "Baelfyre/Orchestra-Compliance-Registry"


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def query_records(
    document: dict[str, Any],
    record_type: str,
    *,
    domain: str | None = None,
    jurisdiction: str | None = None,
) -> list[dict[str, Any]]:
    records = document.get(record_type)
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError(f"record collection {record_type!r} is not an array of objects")
    result = list(records)
    if domain is not None:
        result = [item for item in result if domain in item.get("domains", [])]
    if jurisdiction is not None:
        result = [item for item in result if jurisdiction in item.get("jurisdiction_ids", [])]
    return result


def build_receipt(
    record_type: str,
    *,
    domain: str | None = None,
    jurisdiction: str | None = None,
    root: Path = ROOT,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest_path = root / "registry" / "manifest.json"
    manifest = load_json(manifest_path)
    if manifest.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise ValueError("manifest canonical_repository mismatch")
    records = manifest.get("records")
    if not isinstance(records, dict) or record_type not in records:
        raise KeyError(record_type)
    record_rel = records[record_type]
    if not isinstance(record_rel, str) or not record_rel.startswith("registry/"):
        raise ValueError(f"unsafe record path for {record_type}")
    record_path = root / record_rel
    document = load_json(record_path)
    result = query_records(document, record_type, domain=domain, jurisdiction=jurisdiction)
    result_context = {
        "record_type": record_type,
        "filters": {"domain": domain, "jurisdiction": jurisdiction},
        "count": len(result),
        "records": result,
    }
    receipt = {
        "schema_version": "orchestra.compliance-registry.query-receipt.v1",
        "authority": "NONE_EVIDENCE_ONLY",
        "registry_authority_realm": "EDITABLE_REGISTRY_STATE",
        "publication_trust": "NOT_ESTABLISHED_BY_LOCAL_QUERY",
        "canonical_repository": CANONICAL_REPOSITORY,
        "registry_version": manifest["registry_version"],
        "release_sequence": manifest["release_sequence"],
        "registry_status": manifest["status"],
        "manifest_path": "registry/manifest.json",
        "manifest_sha256": sha256(manifest_path.read_bytes()),
        "record_path": record_rel,
        "record_sha256": sha256(record_path.read_bytes()),
        "record_type": record_type,
        "filters": {"domain": domain, "jurisdiction": jurisdiction},
        "result_count": len(result),
        "result_semantic_sha256": sha256(canonical(result_context)),
        "external_reverification_required_before_trust_or_mutation": True,
        "promotion_from_receipt_forbidden": True,
    }
    validate_receipt(receipt, root=root)
    return receipt, result


def validate_receipt(receipt: dict[str, Any], *, root: Path = ROOT) -> None:
    schema = load_json(root / "schema" / "query-receipt.schema.json")
    validate_value(receipt, schema, "query_receipt")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a non-authorizing Registry query receipt")
    parser.add_argument(
        "record",
        choices=["sources", "obligations", "jurisdictions", "providers", "source_status", "review_due"],
    )
    parser.add_argument("--domain")
    parser.add_argument("--jurisdiction")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    receipt, _ = build_receipt(args.record, domain=args.domain, jurisdiction=args.jurisdiction)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
