from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import validate_schema_contracts

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class SchemaContractTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for name in ("registry", "machine", "schema"):
            shutil.copytree(ROOT / name, root / name)
        return temp, root

    def test_repository_machine_records_match_closed_contracts(self) -> None:
        self.assertEqual([], validate_schema_contracts.validate(ROOT))

    def test_unknown_source_property_fails_closed(self) -> None:
        temp, root = self.fixture()
        try:
            path = root / "registry" / "sources.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["sources"][0]["surprise"] = "not in v1 contract"
            write_json(path, doc)
            self.assertIn("field coverage mismatch", validate_schema_contracts.validate(root)[0])
        finally:
            temp.cleanup()

    def test_duplicate_obligation_evidence_is_rejected(self) -> None:
        temp, root = self.fixture()
        try:
            path = root / "registry" / "obligations.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            evidence = doc["obligations"][0]["required_evidence"]
            evidence.append(evidence[0])
            write_json(path, doc)
            self.assertIn("duplicate array items", validate_schema_contracts.validate(root)[0])
        finally:
            temp.cleanup()

    def test_invalid_review_date_is_rejected_by_schema_contract(self) -> None:
        temp, root = self.fixture()
        try:
            path = root / "registry" / "review-due.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["entries"][0]["next_review_due"] = "not-a-date"
            write_json(path, doc)
            self.assertIn("invalid ISO date", validate_schema_contracts.validate(root)[0])
        finally:
            temp.cleanup()

    def test_schema_live_field_coverage_mismatch_is_rejected(self) -> None:
        temp, root = self.fixture()
        try:
            path = root / "schema" / "source.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["properties"].pop("title")
            write_json(path, schema)
            self.assertIn("field coverage mismatch", validate_schema_contracts.validate(root)[0])
        finally:
            temp.cleanup()

    def test_machine_policy_unknown_field_is_rejected(self) -> None:
        temp, root = self.fixture()
        try:
            path = root / "machine" / "representation-policy.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["unreviewed_authority"] = True
            write_json(path, doc)
            self.assertIn("unexpected property", validate_schema_contracts.validate(root)[0])
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
