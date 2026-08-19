from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import validate_source_provenance

ROOT = Path(__file__).resolve().parents[1]


class SourceProvenanceTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(ROOT / "registry", root / "registry")
        return temp, root

    def test_repository_sources_use_official_primary_provenance(self) -> None:
        self.assertEqual([], validate_source_provenance.validate(ROOT))

    def test_secondary_social_source_is_rejected(self) -> None:
        temp, root = self.fixture()
        try:
            path = root / "registry" / "sources.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            source = document["sources"][0]
            source["canonical_url"] = "https://www.wikipedia.org/example"
            source["citation"]["official_url"] = source["canonical_url"]
            source["verification"]["authority_domain"] = "wikipedia.org"
            path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            errors = validate_source_provenance.validate(root)
            self.assertTrue(any("prohibited" in error for error in errors))
        finally:
            temp.cleanup()

    def test_citation_url_drift_is_rejected(self) -> None:
        temp, root = self.fixture()
        try:
            path = root / "registry" / "sources.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["sources"][0]["citation"]["official_url"] = "https://privacy.gov.ph/"
            path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            errors = validate_source_provenance.validate(root)
            self.assertTrue(any("official_url must equal canonical_url" in error for error in errors))
        finally:
            temp.cleanup()

    def test_verification_cannot_predate_gathering(self) -> None:
        temp, root = self.fixture()
        try:
            path = root / "registry" / "sources.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["sources"][0]["gathered_at"] = "2026-08-20"
            path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            errors = validate_source_provenance.validate(root)
            self.assertTrue(any("verified_at cannot precede gathered_at" in error for error in errors))
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
