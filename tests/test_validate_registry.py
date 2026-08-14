from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import validate_registry

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class RegistryValidatorTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(ROOT / "registry", root / "registry")
        return temp, root

    def test_repository_fixture_is_valid(self):
        self.assertEqual([], validate_registry.validate(ROOT))

    def test_manifest_record_path_drift_is_rejected(self):
        temp, root = self.fixture()
        try:
            manifest_path = root / "registry" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["records"]["sources"] = "../outside.json"
            write_json(manifest_path, manifest)
            self.assertIn("records map", validate_registry.validate(root)[0])
        finally:
            temp.cleanup()

    def test_unsafe_registry_version_is_rejected(self):
        temp, root = self.fixture()
        try:
            manifest_path = root / "registry" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["registry_version"] = "../escape"
            write_json(manifest_path, manifest)
            self.assertIn("safe version token", validate_registry.validate(root)[0])
        finally:
            temp.cleanup()

    def test_source_status_must_reference_known_source(self):
        temp, root = self.fixture()
        try:
            path = root / "registry" / "source-status.json"
            write_json(path, {"schema_version": 1, "entries": [{"source_id": "SRC-MISSING", "status": "VERIFIED_CURRENT"}]})
            self.assertIn("unknown source", validate_registry.validate(root)[0])
        finally:
            temp.cleanup()

    def test_review_due_requires_iso_date(self):
        temp, root = self.fixture()
        try:
            sources_path = root / "registry" / "sources.json"
            write_json(
                sources_path,
                {
                    "schema_version": 1,
                    "sources": [
                        {
                            "source_id": "SRC-1",
                            "canonical_url": "https://example.com/source",
                            "jurisdiction_ids": ["PH"],
                            "domains": ["privacy"],
                            "verification": {"status": "VERIFIED_CURRENT"},
                        }
                    ],
                },
            )
            due_path = root / "registry" / "review-due.json"
            write_json(due_path, {"schema_version": 1, "entries": [{"source_id": "SRC-1", "next_review_due": "not-a-date"}]})
            self.assertIn("invalid next_review_due", validate_registry.validate(root)[0])
        finally:
            temp.cleanup()

    def test_trusted_release_requires_source_status_coverage(self):
        temp, root = self.fixture()
        try:
            sources_path = root / "registry" / "sources.json"
            write_json(
                sources_path,
                {
                    "schema_version": 1,
                    "sources": [
                        {
                            "source_id": "SRC-1",
                            "canonical_url": "https://example.com/source",
                            "jurisdiction_ids": ["PH"],
                            "domains": ["privacy"],
                            "verification": {"status": "VERIFIED_CURRENT"},
                        }
                    ],
                },
            )
            manifest_path = root / "registry" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["status"] = "TRUSTED_RELEASE"
            manifest["release_sequence"] = 1
            manifest["record_counts"]["sources"] = 1
            write_json(manifest_path, manifest)
            self.assertIn("source-status coverage mismatch", validate_registry.validate(root)[0])
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
