from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ReadmeMachineIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = load("README.json")
        cls.manifest = load("registry/manifest.json")
        cls.jurisdictions = load("registry/jurisdictions.json")["jurisdictions"]
        cls.providers = load("registry/providers.json")["providers"]
        cls.sources = load("registry/sources.json")["sources"]
        cls.obligations = load("registry/obligations.json")["obligations"]
        cls.publication = load("machine/publication-state.json")
        cls.representation = load("machine/representation-policy.json")
        cls.provenance_audit = load("machine/source-provenance-audit.v1.json")

    def test_machine_index_identity(self) -> None:
        self.assertEqual("README.md", self.index["human_readme"])
        self.assertEqual("machine_repository_index", self.index["document_role"])
        self.assertEqual("DERIVED_AND_PARITY_VALIDATED_PROJECTION", self.index["authority"])

    def test_source_state_matches_manifest(self) -> None:
        source_state = self.index["source_state"]
        self.assertEqual("registry/manifest.json", source_state["authority_path"])
        self.assertEqual(self.manifest["registry_version"], source_state["registry_version"])
        self.assertEqual(self.manifest["release_sequence"], source_state["release_sequence"])
        self.assertEqual(self.manifest["status"], source_state["status"])
        self.assertEqual(self.manifest["record_counts"], source_state["record_counts"])

    def test_trusted_release_matches_publication_state(self) -> None:
        expected = self.publication["trusted_release"]
        actual = self.index["trusted_release"]
        for key in (
            "state",
            "tag",
            "registry_version",
            "release_sequence",
            "target_commit",
            "release_manifest_sha256",
            "bundle_sha256",
        ):
            self.assertEqual(expected[key], actual[key], key)
        self.assertTrue(actual["publication_reverification_required"])

    def test_registry_record_paths_match_manifest(self) -> None:
        indexed = self.index["records"]
        for record_name, path in self.manifest["records"].items():
            self.assertIn(record_name, indexed)
            self.assertEqual(path, indexed[record_name]["path"])
            self.assertTrue((ROOT / path).is_file())

    def test_jurisdiction_coverage_matches_registry(self) -> None:
        actual = {
            item["jurisdiction_id"]: item
            for item in self.index["coverage"]["jurisdictions"]
        }
        expected = {item["jurisdiction_id"]: item for item in self.jurisdictions}
        self.assertEqual(set(expected), set(actual))

        source_counts: Counter[str] = Counter()
        obligation_counts: Counter[str] = Counter()
        available_domains: dict[str, set[str]] = {key: set() for key in expected}

        for source in self.sources:
            for jurisdiction_id in source["jurisdiction_ids"]:
                source_counts[jurisdiction_id] += 1
                available_domains[jurisdiction_id].update(source["domains"])

        for obligation in self.obligations:
            for jurisdiction_id in obligation["jurisdiction_ids"]:
                obligation_counts[jurisdiction_id] += 1
                available_domains[jurisdiction_id].update(obligation["domains"])

        for jurisdiction_id, registry_record in expected.items():
            indexed = actual[jurisdiction_id]
            for key in ("jurisdiction_id", "name", "kind", "status"):
                self.assertEqual(registry_record[key], indexed[key], f"{jurisdiction_id}:{key}")
            self.assertEqual(source_counts[jurisdiction_id], indexed["source_count"])
            self.assertEqual(obligation_counts[jurisdiction_id], indexed["obligation_count"])
            self.assertTrue(set(indexed["current_scope"]).issubset(available_domains[jurisdiction_id]))

    def test_provider_coverage_matches_registry(self) -> None:
        indexed = {
            item["provider_id"]: item
            for item in self.index["coverage"]["providers"]
        }
        expected = {item["provider_id"]: item for item in self.providers}
        self.assertEqual(expected, indexed)

    def test_representation_policy_binds_readme_pair(self) -> None:
        pair = self.representation["repository_overview_pair"]
        self.assertEqual("README.md", pair["human"])
        self.assertEqual("README.json", pair["machine"])
        self.assertEqual("COMPACT_HUMAN_ORIENTATION", pair["human_role"])
        self.assertEqual("COMPLETE_MACHINE_REPOSITORY_INDEX", pair["machine_role"])
        self.assertEqual(
            "DERIVED_AND_PARITY_VALIDATED_PROJECTION",
            pair["machine_index_authority"],
        )
        self.assertEqual("README.json", self.representation["machine_authority"]["repository_index"])

    def test_machine_index_binds_latest_source_provenance_audit(self) -> None:
        source_model = self.index["source_model"]
        audit = source_model["latest_provenance_audit"]
        self.assertEqual("OFFICIAL_PRIMARY_ONLY", source_model["canonical_source_policy"])
        self.assertFalse(source_model["wikipedia_allowed_as_canonical_source"])
        self.assertFalse(source_model["social_media_allowed_as_canonical_source"])
        self.assertEqual(self.provenance_audit["audited_at"], audit["audited_at"])
        self.assertEqual(self.provenance_audit["summary"]["audited_source_count"], audit["audited_sources"])
        self.assertEqual(self.provenance_audit["summary"]["rechecked_obligation_count"], audit["rechecked_obligations"])
        self.assertEqual(self.provenance_audit["summary"]["audit_result"], audit["result"])
        self.assertEqual(
            "machine/source-provenance-audit.v1.json",
            self.index["records"]["source_provenance_audit"]["path"],
        )
        self.assertTrue((ROOT / self.index["documentation"]["human"]["source_provenance_audit"]).is_file())
        self.assertTrue((ROOT / self.index["documentation"]["machine"]["source_provenance_audit"]).is_file())


if __name__ == "__main__":
    unittest.main()
