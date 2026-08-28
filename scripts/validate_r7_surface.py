from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from scripts import r7_query_gateway
    from scripts.validate_schema_contracts import ContractError, validate_value
except ImportError:
    import r7_query_gateway
    from validate_schema_contracts import ContractError, validate_value

ROOT = Path(__file__).resolve().parents[1]
SURFACE_PATH = ROOT / "machine" / "r7-surface.v1.json"
SURFACE_SCHEMA_PATH = ROOT / "schema" / "r7-surface.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "schema" / "r7-query-receipt.schema.json"
CAPABILITIES_PATH = ROOT / "registry" / "capabilities.json"
ARCHITECTURE_PATH = ROOT / "docs" / "TOKEN_EFFICIENT_QUERY_ARCHITECTURE_R7.md"
EXPECTED_SUPPORTED = {
    "cap.query.projection.v1",
    "cap.query.relationships.v1",
    "cap.query.indexed-read.v1",
    "cap.query.budget.v1",
}
MCP_CAPABILITY = "cap.transport.mcp.v1"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT).as_posix()} must contain an object")
    return value


def validate(root: Path = ROOT) -> list[str]:
    try:
        surface_path = root / SURFACE_PATH.relative_to(ROOT)
        surface_schema_path = root / SURFACE_SCHEMA_PATH.relative_to(ROOT)
        receipt_schema_path = root / RECEIPT_SCHEMA_PATH.relative_to(ROOT)
        capabilities_path = root / CAPABILITIES_PATH.relative_to(ROOT)
        architecture_path = root / ARCHITECTURE_PATH.relative_to(ROOT)

        surface = load(surface_path)
        surface_schema = load(surface_schema_path)
        validate_value(surface, surface_schema, "r7_surface")

        receipt_schema = load(receipt_schema_path)
        if receipt_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ValueError("R7 query receipt must use JSON Schema draft 2020-12")
        if receipt_schema.get("type") != "object" or receipt_schema.get("additionalProperties") is not False:
            raise ValueError("R7 query receipt contract must be a closed object")

        capability_doc = load(capabilities_path)
        capability_rows = capability_doc.get("capabilities")
        if not isinstance(capability_rows, list):
            raise ValueError("registry/capabilities.json capabilities must be an array")
        capabilities = {row.get("capability_id"): row for row in capability_rows if isinstance(row, dict)}
        for capability_id in EXPECTED_SUPPORTED:
            row = capabilities.get(capability_id)
            if not isinstance(row, dict):
                raise ValueError(f"missing stable R7 capability {capability_id}")
            if row.get("contract_version") != "1.0.0" or row.get("status") != "SUPPORTED":
                raise ValueError(f"stable R7 capability contract mismatch for {capability_id}")
            if row.get("optional") is not True:
                raise ValueError(f"R7 optimization capability must remain optional: {capability_id}")
        if MCP_CAPABILITY in capabilities:
            raise ValueError("cap.transport.mcp.v1 must not be published before R7.7 implementation")

        architecture = architecture_path.read_text(encoding="utf-8")
        if "IMPLEMENTED_STABLE_DIRECT_SURFACE_R7_1_R7_6" not in architecture:
            raise ValueError("R7 architecture status does not declare the stable direct surface")
        if "R7.7_NOT_IMPLEMENTED" not in architecture:
            raise ValueError("R7 architecture must preserve the MCP implementation boundary")

        registry = r7_query_gateway.load_typed_registry(root)
        r7_query_gateway.build_relationships(registry)
        gateway = r7_query_gateway.RegistryQueryGateway(root=root)
        result = gateway.query(
            r7_query_gateway.QuerySpec(
                record_type="obligations",
                domain="privacy",
                projection="EVIDENCE",
                limit=2,
                representation="JSON",
            )
        )
        if result.get("backend") != "DIRECT_LOCAL_JSON_QUERY":
            raise ValueError("editable Registry validation must use the direct JSON fallback")
        if result.get("receipt", {}).get("authority_expansion") is not False:
            raise ValueError("R7 receipt must not expand authority")
        return []
    except (OSError, json.JSONDecodeError, ValueError, ContractError, r7_query_gateway.R7Error) as exc:
        return [str(exc)]


def main() -> int:
    errors = validate(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("REGISTRY_R7_STABLE_DIRECT_SURFACE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
