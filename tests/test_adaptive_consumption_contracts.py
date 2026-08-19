from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import release_delta, validate_schema_contracts

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class AdaptiveConsumptionContractTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        temp = tempfile.TemporaryDirectory()
        base = Path(temp.name) / "base"
        target = Path(temp.name) / "target"
        for destination in (base, target):
            shutil.copytree(ROOT / "registry", destination / "registry")
            shutil.copytree(ROOT / "schema", destination / "schema")
            shutil.copytree(ROOT / "machine", destination / "machine")
        return temp, base, target

    def test_repository_contracts_validate(self) -> None:
        self.assertEqual([], validate_schema_contracts.validate(ROOT))

    def test_capability_ids_are_unique_and_non_authorizing(self) -> None:
        doc = json.loads((ROOT / "registry" / "capabilities.json").read_text(encoding="utf-8"))
        ids = [item["capability_id"] for item in doc["capabilities"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual("DESCRIPTIVE_NON_AUTHORIZING", doc["authority"])
        self.assertTrue(all(value is False for value in doc["authority_boundaries"].values()))

    def test_delta_is_unchanged_for_identical_state(self) -> None:
        temp, base, target = self.fixture()
        try:
            result = release_delta.build_delta(base, target)
            self.assertEqual("UNCHANGED", result["disposition"])
            self.assertEqual([], result["changed_record_types"])
            self.assertFalse(result["requires_human_review"])
        finally:
            temp.cleanup()

    def test_capability_addition_is_compatible_scoped_change(self) -> None:
        temp, base, target = self.fixture()
        try:
            path = target / "registry" / "capabilities.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["capabilities"].append({
                "capability_id": "cap.audit-stream.v1",
                "contract_version": "1.0.0",
                "status": "EXPERIMENTAL",
                "required_records": ["capabilities"],
                "optional": True,
                "fallback": "IGNORE_OPTIONAL_CAPABILITY",
            })
            write_json(path, doc)
            result = release_delta.build_delta(base, target)
            self.assertEqual("COMPATIBLE_SCOPED_CHANGE", result["disposition"])
            self.assertIn("cap.audit-stream.v1", result["affected"]["capability_ids"])
        finally:
            temp.cleanup()

    def test_capability_contract_mutation_fails_closed(self) -> None:
        temp, base, target = self.fixture()
        try:
            path = target / "registry" / "capabilities.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["capabilities"][0]["contract_version"] = "2.0.0"
            write_json(path, doc)
            result = release_delta.build_delta(base, target)
            self.assertEqual("UNSUPPORTED_CAPABILITY_CHANGE", result["disposition"])
        finally:
            temp.cleanup()

    def test_source_status_change_requires_scoped_revalidation(self) -> None:
        temp, base, target = self.fixture()
        try:
            path = target / "registry" / "source-status.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["entries"][0]["status"] = "CURRENT_WITH_PENDING_CHANGE"
            write_json(path, doc)
            result = release_delta.build_delta(base, target)
            self.assertEqual("REVALIDATION_REQUIRED", result["disposition"])
            self.assertEqual([doc["entries"][0]["source_id"]], result["affected"]["source_ids"])
        finally:
            temp.cleanup()

    def test_substantive_source_change_requires_human_review(self) -> None:
        temp, base, target = self.fixture()
        try:
            path = target / "registry" / "sources.json"
            doc = json.loads(path.read_text(encoding="utf-8"))
            doc["sources"][0]["title"] = doc["sources"][0]["title"] + " reviewed change"
            write_json(path, doc)
            result = release_delta.build_delta(base, target)
            self.assertEqual("HUMAN_REVIEW_REQUIRED", result["disposition"])
            self.assertTrue(result["requires_human_review"])
        finally:
            temp.cleanup()

    def test_delta_digest_is_stable(self) -> None:
        temp, base, target = self.fixture()
        try:
            first = release_delta.build_delta(base, target)
            second = release_delta.build_delta(base, target)
            self.assertEqual(first["digest"], second["digest"])
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
