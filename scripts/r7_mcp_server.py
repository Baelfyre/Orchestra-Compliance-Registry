#!/usr/bin/env python3
"""Read-only MCP transport for the Registry R7 query gateway.

MCP is transport only. Every tool delegates to the deterministic R7 direct surface or
an existing Registry evidence function. No tool can mutate Registry records, create a
release, infer legal applicability, or expand Orchestra authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

try:
    from scripts import r7_query_gateway, r7_trusted_release, release_delta
except ImportError:
    import r7_query_gateway  # type: ignore
    import r7_trusted_release  # type: ignore
    import release_delta  # type: ignore

MCP_CAPABILITY = "cap.transport.mcp.v1"
SERVER_NAME = "orchestra-compliance-registry-r7"
SERVER_VERSION = "1.0.0"


class RegistryMcpError(ValueError):
    pass


class RegistryMcpAdapter:
    """Pure read adapter that is independently testable from the MCP SDK transport."""

    def __init__(
        self,
        gateway: r7_query_gateway.RegistryQueryGateway,
        *,
        delta_roots: Mapping[str, Path] | None = None,
    ) -> None:
        self.gateway = gateway
        roots = dict(delta_roots or {"current": gateway.root})
        if "current" not in roots:
            roots["current"] = gateway.root
        self.delta_roots = {name: Path(path).resolve() for name, path in roots.items()}

    @staticmethod
    def _query_spec(arguments: Mapping[str, Any]) -> r7_query_gateway.QuerySpec:
        fields = arguments.get("fields", ())
        if fields is None:
            fields = ()
        if not isinstance(fields, (list, tuple)) or not all(isinstance(value, str) for value in fields):
            raise RegistryMcpError("fields must be an array of strings")
        return r7_query_gateway.QuerySpec(
            record_type=str(arguments.get("record_type", "")),
            domain=arguments.get("domain"),
            jurisdiction=arguments.get("jurisdiction"),
            provider=arguments.get("provider"),
            source_id=arguments.get("source_id"),
            obligation_id=arguments.get("obligation_id"),
            projection=str(arguments.get("projection", "SUMMARY")).upper(),
            fields=tuple(fields),
            include_freshness=bool(arguments.get("include_freshness", True)),
            limit=arguments.get("limit", 50),
            cursor=arguments.get("cursor"),
            maximum_context_bytes=arguments.get("maximum_context_bytes"),
            representation=str(arguments.get("representation", "AUTO")).upper(),
        )

    def registry_status(self) -> dict[str, Any]:
        value = dict(self.gateway.status())
        caps = list(value.get("capabilities", []))
        if MCP_CAPABILITY in self.gateway.registry.collections["capabilities"] and MCP_CAPABILITY not in caps:
            caps.append(MCP_CAPABILITY)
        value.update(
            {
                "transport": "MCP_STDIO_READ_ONLY",
                "mcp_capability": MCP_CAPABILITY,
                "capabilities": sorted(caps),
                "registry_mutation": False,
                "trusted_release_publication": False,
                "legal_applicability_inference": False,
                "authority_expansion": False,
            }
        )
        return value

    def registry_query(self, **arguments: Any) -> dict[str, Any]:
        result = dict(self.gateway.query(self._query_spec(arguments)))
        result["transport_adapter"] = "MCP_STDIO_READ_ONLY"
        result["authority_expansion"] = False
        return result

    def registry_get(
        self,
        entity_type: str,
        entity_id: str,
        projection: str = "FULL",
        include_freshness: bool = True,
        representation: str = "JSON",
    ) -> dict[str, Any]:
        if entity_type == "source":
            result = self.registry_query(
                record_type="sources",
                source_id=entity_id,
                projection=projection,
                include_freshness=include_freshness,
                limit=1,
                representation=representation,
            )
        elif entity_type == "obligation":
            result = self.registry_query(
                record_type="obligations",
                obligation_id=entity_id,
                projection=projection,
                include_freshness=include_freshness,
                limit=1,
                representation=representation,
            )
        else:
            raise RegistryMcpError("registry_get supports source or obligation")
        if result.get("count") != 1:
            raise KeyError(entity_id)
        return result

    def registry_relations(self, entity_type: str, entity_id: str) -> dict[str, Any]:
        result = dict(self.gateway.relations(entity_type, entity_id))
        result["transport_adapter"] = "MCP_STDIO_READ_ONLY"
        result["authority_expansion"] = False
        return result

    def registry_freshness(self, source_id: str) -> dict[str, Any]:
        result = self.registry_get("source", source_id, projection="EVIDENCE", include_freshness=True)
        record = result["records"][0]
        freshness = record.get("_freshness")
        if not isinstance(freshness, dict):
            raise RegistryMcpError("freshness evidence missing from R7 source projection")
        return {
            "schema_version": "orchestra.compliance-registry.r7-mcp-freshness.v1",
            "authority": "EVIDENCE_ONLY_NON_AUTHORIZING",
            "source_id": source_id,
            "freshness": freshness,
            "query_receipt": result["receipt"],
            "transport_adapter": "MCP_STDIO_READ_ONLY",
            "authority_expansion": False,
        }

    def registry_delta(self, base: str, target: str = "current") -> dict[str, Any]:
        if base not in self.delta_roots or target not in self.delta_roots:
            raise RegistryMcpError("delta roots must be operator-configured labels")
        result = dict(release_delta.build_delta(self.delta_roots[base], self.delta_roots[target]))
        result["transport_adapter"] = "MCP_STDIO_READ_ONLY"
        result["authority_expansion"] = False
        return result

    def call(self, name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
        args = dict(arguments or {})
        if name == "registry_status":
            if args:
                raise RegistryMcpError("registry_status accepts no arguments")
            return self.registry_status()
        if name == "registry_query":
            return self.registry_query(**args)
        if name == "registry_get":
            return self.registry_get(**args)
        if name == "registry_relations":
            return self.registry_relations(**args)
        if name == "registry_freshness":
            return self.registry_freshness(**args)
        if name == "registry_delta":
            return self.registry_delta(**args)
        raise RegistryMcpError(f"unknown MCP tool: {name}")


def create_mcp_server(adapter: RegistryMcpAdapter):
    """Create the official MCP Python SDK v2 server lazily.

    The dependency is intentionally isolated to the transport boundary so Registry
    query semantics remain usable without MCP installed.
    """
    try:
        from mcp.server import MCPServer
    except ImportError as exc:  # pragma: no cover - exercised by CLI failure path
        raise RegistryMcpError("MCP SDK v2 is required; install requirements-mcp.txt") from exc

    mcp = MCPServer(
        SERVER_NAME,
        version=SERVER_VERSION,
        instructions=(
            "Read-only Orchestra Compliance Registry R7 transport. Registry JSON remains authority. "
            "Tool results are evidence/non-authoritative and cannot publish releases or infer legal applicability."
        ),
    )

    @mcp.tool()
    def registry_status() -> dict[str, Any]:
        """Return Registry/R7 status and evidence-only capability information."""
        return adapter.registry_status()

    @mcp.tool()
    def registry_query(
        record_type: str,
        domain: str | None = None,
        jurisdiction: str | None = None,
        provider: str | None = None,
        source_id: str | None = None,
        obligation_id: str | None = None,
        projection: str = "SUMMARY",
        fields: list[str] | None = None,
        include_freshness: bool = True,
        limit: int = 50,
        cursor: str | None = None,
        maximum_context_bytes: int | None = None,
        representation: str = "AUTO",
    ) -> dict[str, Any]:
        """Run the shared deterministic R7 read query with bounded projection/context."""
        return adapter.registry_query(
            record_type=record_type,
            domain=domain,
            jurisdiction=jurisdiction,
            provider=provider,
            source_id=source_id,
            obligation_id=obligation_id,
            projection=projection,
            fields=fields or [],
            include_freshness=include_freshness,
            limit=limit,
            cursor=cursor,
            maximum_context_bytes=maximum_context_bytes,
            representation=representation,
        )

    @mcp.tool()
    def registry_get(
        entity_type: str,
        entity_id: str,
        projection: str = "FULL",
        include_freshness: bool = True,
        representation: str = "JSON",
    ) -> dict[str, Any]:
        """Fetch one exact source or obligation through the shared R7 gateway."""
        return adapter.registry_get(entity_type, entity_id, projection, include_freshness, representation)

    @mcp.tool()
    def registry_relations(entity_type: str, entity_id: str) -> dict[str, Any]:
        """Return deterministic derived relationships for one Registry entity."""
        return adapter.registry_relations(entity_type, entity_id)

    @mcp.tool()
    def registry_freshness(source_id: str) -> dict[str, Any]:
        """Return exact source freshness/review evidence and the bound query receipt."""
        return adapter.registry_freshness(source_id)

    @mcp.tool()
    def registry_delta(base: str, target: str = "current") -> dict[str, Any]:
        """Compare operator-configured Registry roots using the existing release-delta contract."""
        return adapter.registry_delta(base, target)

    return mcp


def _delta_root(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--delta-root must be NAME=PATH")
    name, raw_path = value.split("=", 1)
    name = name.strip()
    if not name or name == "current":
        raise argparse.ArgumentTypeError("delta root label must be non-empty and not 'current'")
    return name, Path(raw_path).resolve()


def build_adapter_from_args(args: argparse.Namespace) -> RegistryMcpAdapter:
    root = Path(args.root).resolve()
    index_path = Path(args.index).resolve() if args.index else None
    release_identity = None
    if args.trusted_manifest_sha256:
        verified = r7_trusted_release.load_installed_identity(root, args.trusted_manifest_sha256)
        release_identity = verified.identity
        if index_path is None:
            raise RegistryMcpError("trusted release identity requires --index for indexed MCP mode")
    elif index_path is not None:
        raise RegistryMcpError("--index requires --trusted-manifest-sha256")
    gateway = r7_query_gateway.RegistryQueryGateway(root, index_path, release_identity)
    roots = {"current": root}
    for name, path in args.delta_root:
        if name in roots:
            raise RegistryMcpError(f"duplicate delta root label: {name}")
        roots[name] = path
    return RegistryMcpAdapter(gateway, delta_roots=roots)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Registry R7 MCP stdio server")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--index")
    parser.add_argument("--trusted-manifest-sha256")
    parser.add_argument("--delta-root", action="append", type=_delta_root, default=[])
    parser.add_argument("--describe", action="store_true", help="print transport status without starting MCP")
    args = parser.parse_args(argv)
    try:
        adapter = build_adapter_from_args(args)
        if args.describe:
            print(json.dumps(adapter.registry_status(), indent=2, sort_keys=True))
            return 0
        server = create_mcp_server(adapter)
        server.run()
        return 0
    except (RegistryMcpError, r7_query_gateway.R7Error, r7_trusted_release.TrustedReleaseError) as exc:
        print(f"R7_MCP_FAIL={exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
