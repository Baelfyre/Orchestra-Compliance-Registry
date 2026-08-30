from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import r7_query_gateway
from scripts.validate_schema_contracts import ContractError, validate_value

ROOT = Path(__file__).resolve().parents[1]


class R7QueryGatewayTests(unittest.TestCase):
    def test_surface_contract_and_entry_gate(self) -> None:
        surface = json.loads((ROOT / "machine" / "r7-surface.v1.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schema" / "r7-surface.schema.json").read_text(encoding="utf-8"))
        validate_value(surface, schema, "r7_surface")
        self.assertEqual(
            "IMPLEMENTED_R7_1_R7_9_TRUSTED_V0_4_0_PUBLISHED_O7_7_CONFORMANCE_COMPLETE",
            surface["implementation"]["status"],
        )
        self.assertTrue(surface["orchestra_entry_gate"]["satisfied"])
        self.assertTrue(surface["transport"]["mcp_available"])
        self.assertEqual("IMPLEMENTED_READ_ONLY_TRANSPORT", surface["transport"]["mcp_disposition"])
        self.assertTrue(surface["release_boundary"]["published"])
        self.assertEqual(
            "PUBLISHED_IMMUTABLE_VERIFIED_AND_O7_7_CONFORMANCE_COMPLETE",
            surface["release_boundary"]["publication_state"],
        )

    def test_typed_registry_and_relationships_are_deterministic(self) -> None:
        registry = r7_query_gateway.load_typed_registry(ROOT)
        first = r7_query_gateway.build_relationships(registry)
        second = r7_query_gateway.build_relationships(registry)
        self.assertEqual(r7_query_gateway.relationship_digest(first), r7_query_gateway.relationship_digest(second))
        self.assertEqual(set(registry.collections["sources"]), set(registry.collections["source_status"]))
        self.assertEqual(set(registry.collections["sources"]), set(registry.collections["review_due"]))
        for obligation_id, source_ids in first["obligation_source"].items():
            for source_id in source_ids:
                self.assertIn(obligation_id, first["source_obligation"][source_id])

    def test_direct_query_preserves_exact_ids_across_projection(self) -> None:
        gateway = r7_query_gateway.RegistryQueryGateway(root=ROOT)
        summary = gateway.query(
            r7_query_gateway.QuerySpec(
                record_type="obligations",
                jurisdiction="PH",
                projection="SUMMARY",
                fields=("title", "summary"),
                limit=3,
                representation="JSON",
            )
        )
        self.assertEqual("DIRECT_LOCAL_JSON_QUERY", summary["backend"])
        self.assertGreater(summary["count"], 0)
        for record in summary["records"]:
            self.assertIn("obligation_id", record)
        receipt = summary["receipt"]
        self.assertEqual(summary["count"], len(receipt["exact_obligation_ids"]))
        self.assertFalse(receipt["authority_expansion"])
        self.assertFalse(receipt["model_authored_integrity_repair"])

    def test_context_budget_fails_closed_if_response_cannot_fit(self) -> None:
        gateway = r7_query_gateway.RegistryQueryGateway(root=ROOT)
        with self.assertRaises(r7_query_gateway.ContextBudgetExceeded):
            gateway.query(
                r7_query_gateway.QuerySpec(
                    record_type="obligations",
                    projection="FULL",
                    maximum_context_bytes=100,
                    representation="JSON",
                )
            )

    def test_editable_registry_cannot_build_trusted_index(self) -> None:
        identity = r7_query_gateway.ReleaseIdentity(
            registry_version="0.2.0-dev.1",
            release_tag="registry-v0.2.0-dev.1",
            release_sequence=0,
            release_manifest_sha256="a" * 64,
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(r7_query_gateway.R7Error):
                r7_query_gateway.build_index(Path(directory) / "index.sqlite", identity, root=ROOT)

    def test_index_and_direct_query_have_semantic_parity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "registry-fixture"
            shutil.copytree(ROOT / "registry", fixture / "registry")
            shutil.copytree(ROOT / "schema", fixture / "schema")
            manifest_path = fixture / "registry" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update(
                {
                    "registry_version": "0.4.0-test",
                    "release_sequence": 4,
                    "release_tag": "registry-v0.4.0-test",
                    "status": "TRUSTED_RELEASE",
                }
            )
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            release_manifest_path = fixture / "release-manifest.json"
            release_manifest_path.write_text(
                json.dumps(
                    {
                        "canonical_repository": r7_query_gateway.REPOSITORY,
                        "status": "TRUSTED_RELEASE",
                        "registry_version": "0.4.0-test",
                        "release_sequence": 4,
                        "release_tag": "registry-v0.4.0-test",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            identity = r7_query_gateway.ReleaseIdentity(
                registry_version="0.4.0-test",
                release_tag="registry-v0.4.0-test",
                release_sequence=4,
                release_manifest_sha256=r7_query_gateway.digest(release_manifest_path.read_bytes()),
            )
            index_path = fixture / "r7.sqlite"
            r7_query_gateway.build_index(index_path, identity, root=fixture)
            indexed = r7_query_gateway.RegistryQueryGateway(
                root=fixture, index_path=index_path, release_identity=identity
            )
            direct = r7_query_gateway.RegistryQueryGateway(root=fixture)
            spec = r7_query_gateway.QuerySpec(
                record_type="obligations",
                domain="privacy",
                projection="EVIDENCE",
                limit=100,
                representation="JSON",
            )
            indexed_result = indexed.query(spec)
            direct_result = direct.query(spec)
            self.assertEqual(direct_result["records"], indexed_result["records"])
            self.assertEqual(
                direct_result["receipt"]["exact_source_ids"],
                indexed_result["receipt"]["exact_source_ids"],
            )
            self.assertEqual(
                direct_result["receipt"]["exact_obligation_ids"],
                indexed_result["receipt"]["exact_obligation_ids"],
            )

    def test_tampered_receipt_cannot_expand_authority(self) -> None:
        gateway = r7_query_gateway.RegistryQueryGateway(root=ROOT)
        result = gateway.query(r7_query_gateway.QuerySpec(record_type="sources", limit=1))
        tampered = copy.deepcopy(result["receipt"])
        tampered["authority_expansion"] = True
        with self.assertRaises(ContractError):
            r7_query_gateway.validate_r7_receipt(tampered, root=ROOT)


if __name__ == "__main__":
    unittest.main()
