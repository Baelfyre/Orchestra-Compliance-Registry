from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from scripts import r7_mcp_server, r7_query_gateway

ROOT = Path(__file__).resolve().parents[1]


class R7McpAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = r7_query_gateway.RegistryQueryGateway(root=ROOT)
        self.adapter = r7_mcp_server.RegistryMcpAdapter(self.gateway, delta_roots={"current": ROOT, "same": ROOT})

    def test_status_is_read_only_and_non_authorizing(self) -> None:
        value = self.adapter.registry_status()
        self.assertEqual("MCP_STDIO_READ_ONLY", value["transport"])
        self.assertFalse(value["registry_mutation"])
        self.assertFalse(value["trusted_release_publication"])
        self.assertFalse(value["legal_applicability_inference"])
        self.assertFalse(value["authority_expansion"])

    def test_query_reuses_shared_gateway_semantics(self) -> None:
        direct = self.gateway.query(
            r7_query_gateway.QuerySpec("obligations", domain="privacy", projection="EVIDENCE", limit=5, representation="JSON")
        )
        through_mcp = self.adapter.registry_query(
            record_type="obligations", domain="privacy", projection="EVIDENCE", limit=5, representation="JSON"
        )
        for key in direct:
            self.assertEqual(direct[key], through_mcp[key], key)
        self.assertEqual("MCP_STDIO_READ_ONLY", through_mcp["transport_adapter"])
        self.assertFalse(through_mcp["authority_expansion"])

    def test_get_relations_and_freshness_are_evidence_only(self) -> None:
        source_id = sorted(self.gateway.registry.collections["sources"])[0]
        source = self.adapter.registry_get("source", source_id, projection="EVIDENCE")
        self.assertEqual(1, source["count"])
        relations = self.adapter.registry_relations("source", source_id)
        self.assertEqual("DERIVED_NON_AUTHORITATIVE", relations["authority"])
        freshness = self.adapter.registry_freshness(source_id)
        self.assertEqual("EVIDENCE_ONLY_NON_AUTHORIZING", freshness["authority"])
        self.assertEqual(source_id, freshness["freshness"]["source_id"])
        self.assertFalse(freshness["authority_expansion"])

    def test_delta_uses_only_operator_configured_labels(self) -> None:
        value = self.adapter.registry_delta("same", "current")
        self.assertEqual("UNCHANGED", value["disposition"])
        self.assertFalse(value["authority_expansion"])
        with self.assertRaises(r7_mcp_server.RegistryMcpError):
            self.adapter.registry_delta("/tmp/not-an-operator-label", "current")

    def test_unknown_tool_and_invalid_get_fail_closed(self) -> None:
        with self.assertRaises(r7_mcp_server.RegistryMcpError):
            self.adapter.call("registry_mutate", {})
        with self.assertRaises(r7_mcp_server.RegistryMcpError):
            self.adapter.registry_get("jurisdiction", "PH")

    @unittest.skipUnless(importlib.util.find_spec("mcp") is not None, "MCP SDK not installed")
    def test_official_sdk_server_constructs(self) -> None:
        server = r7_mcp_server.create_mcp_server(self.adapter)
        self.assertIsNotNone(server)


if __name__ == "__main__":
    unittest.main()
