from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from scripts import r7_mcp_server, r7_query_gateway
    from scripts.validate_schema_contracts import ContractError, validate_value
except ImportError:
    import r7_mcp_server
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
    "cap.transport.mcp.v1",
}
MCP_CAPABILITY = "cap.transport.mcp.v1"
REQUIRED_MCP_TOOLS = (
    "registry_status",
    "registry_query",
    "registry_get",
    "registry_relations",
    "registry_freshness",
    "registry_delta",
)


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
                raise ValueError(f"R7 optimization/transport capability must remain optional: {capability_id}")
        if capabilities[MCP_CAPABILITY].get("fallback") != "DIRECT_LOCAL_JSON_QUERY":
            raise ValueError("MCP capability fallback must preserve the direct JSON path")

        architecture = architecture_path.read_text(encoding="utf-8")
        if "IMPLEMENTED_R7_1_R7_9_PENDING_TRUSTED_PUBLICATION_AND_O7_7_CONFORMANCE" not in architecture:
            raise ValueError("R7 architecture status does not declare complete R7.1-R7.9 implementation")
        if "IMPLEMENTED_READ_ONLY_TRANSPORT" not in architecture:
            raise ValueError("R7 architecture does not declare the read-only MCP transport")
        if "TOKEN_EFFICIENCY_NOT_CLAIMED_WITHOUT_HOST_MEASUREMENT" not in architecture:
            raise ValueError("R7 architecture must preserve the measured-token evidence boundary")

        for relative in (
            "scripts/r7_mcp_server.py",
            "scripts/r7_trusted_release.py",
            "scripts/r7_benchmark.py",
            "tests/test_r7_mcp_server.py",
            "tests/test_r7_trusted_release.py",
            "tests/test_r7_benchmark.py",
        ):
            if not (root / relative).is_file():
                raise ValueError(f"missing complete R7 surface path: {relative}")

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

        adapter = r7_mcp_server.RegistryMcpAdapter(gateway, delta_roots={"current": root, "same": root})
        status = adapter.registry_status()
        if status.get("transport") != "MCP_STDIO_READ_ONLY" or status.get("authority_expansion") is not False:
            raise ValueError("R7 MCP adapter transport/authority boundary mismatch")
        if MCP_CAPABILITY not in status.get("capabilities", []):
            raise ValueError("R7 MCP adapter did not expose the validated MCP capability")
        if tuple(surface["transport"]["mcp_tools"]) != REQUIRED_MCP_TOOLS:
            raise ValueError("R7 machine state MCP tool set drift")
        through_mcp = adapter.registry_query(
            record_type="obligations",
            domain="privacy",
            projection="EVIDENCE",
            limit=2,
            representation="JSON",
        )
        for key, value in result.items():
            if through_mcp.get(key) != value:
                raise ValueError(f"MCP/direct query parity mismatch for {key}")
        if through_mcp.get("transport_adapter") != "MCP_STDIO_READ_ONLY":
            raise ValueError("MCP query transport evidence missing")
        return []
    except (OSError, json.JSONDecodeError, ValueError, ContractError, r7_query_gateway.R7Error, r7_mcp_server.RegistryMcpError) as exc:
        return [str(exc)]


def main() -> int:
    errors = validate(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("REGISTRY_R7_COMPLETE_SURFACE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
