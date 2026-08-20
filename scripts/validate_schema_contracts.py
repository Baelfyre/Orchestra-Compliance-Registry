from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

RECORD_CONTRACTS = {
    "schema/source.schema.json": ("registry/sources.json", "sources"),
    "schema/obligation.schema.json": ("registry/obligations.json", "obligations"),
    "schema/jurisdiction.schema.json": ("registry/jurisdictions.json", "jurisdictions"),
    "schema/provider.schema.json": ("registry/providers.json", "providers"),
    "schema/source-status.schema.json": ("registry/source-status.json", "entries"),
    "schema/review-due.schema.json": ("registry/review-due.json", "entries"),
}
DOCUMENT_CONTRACTS = {
    "schema/manifest.schema.json": "registry/manifest.json",
    "schema/capability-manifest.schema.json": "registry/capabilities.json",
    "schema/representation-policy.schema.json": "machine/representation-policy.json",
    "schema/publication-state.schema.json": "machine/publication-state.json",
    "schema/readme-machine-index.schema.json": "README.json",
    "schema/source-provenance-audit.schema.json": "machine/source-provenance-audit.v1.json",
    "schema/source-monitor-policy.schema.json": "machine/source-monitor-policy.json",
    "schema/source-monitor-baseline.schema.json": "machine/source-monitor-baseline.v1.json",
}
RELEASE_REQUEST_SCHEMA = "schema/release-request.schema.json"
RELEASE_REQUEST_GLOB = "machine/release-request-v*.json"
STANDALONE_CONTRACTS = (
    "schema/query-receipt.schema.json",
    "schema/source-watch-receipt.schema.json",
    "schema/release-delta.schema.json",
)


class ContractError(ValueError):
    pass


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read {path.as_posix()}: {exc}") from exc


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ContractError(f"unsupported schema type {expected!r}")


def validate_value(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    if "const" in schema and value != schema["const"]:
        raise ContractError(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractError(f"{path}: value {value!r} is outside enum")

    expected_type = schema.get("type")
    if expected_type is not None:
        if isinstance(expected_type, list):
            if not any(_type_matches(value, item) for item in expected_type):
                raise ContractError(f"{path}: type mismatch, expected one of {expected_type}")
        elif not _type_matches(value, expected_type):
            raise ContractError(f"{path}: type mismatch, expected {expected_type}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise ContractError(f"{path}: schema required must be an array")
        missing = [key for key in required if key not in value]
        if missing:
            raise ContractError(f"{path}: missing required keys {missing}")
        min_properties = schema.get("minProperties")
        if min_properties is not None and len(value) < min_properties:
            raise ContractError(f"{path}: requires at least {min_properties} properties")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ContractError(f"{path}: schema properties must be an object")
        additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            if key in properties:
                validate_value(child, properties[key], f"{path}.{key}")
            elif additional is False:
                raise ContractError(f"{path}: unexpected property {key!r}")
            elif isinstance(additional, dict):
                validate_value(child, additional, f"{path}.{key}")

    if isinstance(value, list):
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if minimum is not None and len(value) < minimum:
            raise ContractError(f"{path}: requires at least {minimum} items")
        if maximum is not None and len(value) > maximum:
            raise ContractError(f"{path}: allows at most {maximum} items")
        if schema.get("uniqueItems") is True:
            normalized = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(normalized) != len(set(normalized)):
                raise ContractError(f"{path}: duplicate array items are forbidden")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                validate_value(item, item_schema, f"{path}[{index}]")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(value) < min_length:
            raise ContractError(f"{path}: string shorter than {min_length}")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, value) is None:
            raise ContractError(f"{path}: does not match pattern {pattern!r}")
        if schema.get("format") == "date":
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ContractError(f"{path}: invalid ISO date {value!r}") from exc

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            raise ContractError(f"{path}: value {value} is below minimum {minimum}")


def _assert_closed_schema(schema: dict[str, Any], label: str) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ContractError(f"{label}: must use JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        raise ContractError(f"{label}: top-level contract must be an object")
    if schema.get("additionalProperties") is not False:
        raise ContractError(f"{label}: top-level contract must fail closed on unknown properties")


def _assert_live_field_coverage(schema: dict[str, Any], records: list[dict[str, Any]], label: str) -> None:
    properties = set(schema.get("properties", {}))
    live_fields: set[str] = set()
    for record in records:
        live_fields.update(record)
    if properties != live_fields:
        raise ContractError(
            f"{label}: schema/live field coverage mismatch missing={sorted(live_fields - properties)} "
            f"extra={sorted(properties - live_fields)}"
        )


def validate(root: Path = ROOT) -> list[str]:
    try:
        for schema_rel, (document_rel, collection_key) in RECORD_CONTRACTS.items():
            schema = load(root / schema_rel)
            _assert_closed_schema(schema, schema_rel)
            document = load(root / document_rel)
            if not isinstance(document, dict) or document.get("schema_version") != 1:
                raise ContractError(f"{document_rel}: expected schema_version 1 object")
            records = document.get(collection_key)
            if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
                raise ContractError(f"{document_rel}.{collection_key}: expected array of objects")
            _assert_live_field_coverage(schema, records, schema_rel)
            for index, record in enumerate(records):
                validate_value(record, schema, f"{document_rel}.{collection_key}[{index}]")

        for schema_rel, document_rel in DOCUMENT_CONTRACTS.items():
            schema = load(root / schema_rel)
            _assert_closed_schema(schema, schema_rel)
            validate_value(load(root / document_rel), schema, document_rel)

        release_schema = load(root / RELEASE_REQUEST_SCHEMA)
        _assert_closed_schema(release_schema, RELEASE_REQUEST_SCHEMA)
        release_requests = sorted(root.glob(RELEASE_REQUEST_GLOB))
        if not release_requests:
            raise ContractError(f"{RELEASE_REQUEST_GLOB}: at least one release request is required")
        for request_path in release_requests:
            request_rel = request_path.relative_to(root).as_posix()
            validate_value(load(request_path), release_schema, request_rel)

        for schema_rel in STANDALONE_CONTRACTS:
            _assert_closed_schema(load(root / schema_rel), schema_rel)

        return []
    except ContractError as exc:
        return [str(exc)]


def main() -> int:
    errors = validate(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("REGISTRY_SCHEMA_CONTRACTS_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
