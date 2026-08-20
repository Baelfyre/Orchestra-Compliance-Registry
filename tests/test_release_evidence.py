from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_schema_contracts

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ReleaseEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = load("machine/release-evidence-v0.3.0.json")
        cls.schema = load("schema/release-evidence.schema.json")
        cls.history = load("machine/trusted-release-history.json")
        cls.history_schema = load("schema/trusted-release-history.schema.json")
        cls.publication = load("machine/publication-state.json")
        cls.readme = load("README.json")

    def test_release_evidence_matches_schema(self) -> None:
        validate_schema_contracts.validate_value(
            self.evidence,
            self.schema,
            "machine/release-evidence-v0.3.0.json",
        )

    def test_trusted_release_history_matches_schema(self) -> None:
        validate_schema_contracts.validate_value(
            self.history,
            self.history_schema,
            "machine/trusted-release-history.json",
        )

    def test_release_evidence_matches_publication_state(self) -> None:
        trusted = self.publication["trusted_release"]
        mapping = {
            "release_tag": "tag",
            "release_id": "release_id",
            "registry_version": "registry_version",
            "release_sequence": "release_sequence",
            "source_commit": "target_commit",
            "draft": "draft",
            "prerelease": "prerelease",
            "immutable": "immutable",
            "published_at": "published_at",
            "release_manifest_sha256": "release_manifest_sha256",
            "bundle_sha256": "bundle_sha256",
            "assets": "required_assets",
        }
        for evidence_key, publication_key in mapping.items():
            self.assertEqual(trusted[publication_key], self.evidence[evidence_key], evidence_key)

    def test_readme_trusted_release_matches_evidence(self) -> None:
        trusted = self.readme["trusted_release"]
        self.assertEqual(self.evidence["release_tag"], trusted["tag"])
        self.assertEqual(self.evidence["release_id"], trusted["release_id"])
        self.assertEqual(self.evidence["registry_version"], trusted["registry_version"])
        self.assertEqual(self.evidence["release_sequence"], trusted["release_sequence"])
        self.assertEqual(self.evidence["source_commit"], trusted["target_commit"])
        self.assertEqual(self.evidence["source_tree"], trusted["source_tree"])
        self.assertEqual(self.evidence["published_at"], trusted["published_at"])
        self.assertEqual(self.evidence["immutable"], trusted["immutable"])
        self.assertEqual(self.evidence["release_manifest_sha256"], trusted["release_manifest_sha256"])
        self.assertEqual(self.evidence["bundle_sha256"], trusted["bundle_sha256"])
        self.assertEqual("machine/release-evidence-v0.3.0.json", trusted["release_evidence"])

    def test_history_current_pointer_matches_publication_state(self) -> None:
        trusted = self.publication["trusted_release"]
        self.assertEqual(trusted["tag"], self.history["current_trusted_release"])
        matches = [item for item in self.history["releases"] if item["tag"] == trusted["tag"]]
        self.assertEqual(1, len(matches))
        historical = matches[0]
        for key in (
            "release_id",
            "registry_version",
            "release_sequence",
            "target_commit",
            "draft",
            "prerelease",
            "immutable",
            "published_at",
            "release_manifest_sha256",
            "bundle_sha256",
            "required_assets",
        ):
            self.assertEqual(trusted[key], historical[key], key)

    def test_release_source_is_frozen_and_external_reverification_remains_required(self) -> None:
        self.assertEqual("20eb859db153f17e24c052a13765e982d51cedbf", self.evidence["source_commit"])
        self.assertEqual("763be9062a0c23031c794403dc4592f5db4389b0", self.evidence["source_tree"])
        self.assertTrue(self.evidence["external_reverification_required_before_trust_or_mutation"])
        self.assertTrue(self.history["external_reverification_required_before_trust_or_mutation"])


if __name__ == "__main__":
    unittest.main()
