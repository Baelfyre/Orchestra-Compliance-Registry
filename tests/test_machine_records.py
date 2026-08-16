from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import validate_machine_records

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class RegistryMachineRecordTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(ROOT / "registry", root / "registry")
        return temp, root

    def test_repository_machine_records_are_valid(self):
        self.assertEqual([], validate_machine_records.validate(ROOT))

    def test_markdown_cannot_be_machine_authority(self):
        temp, root = self.fixture()
        try:
            path = root / "registry" / "representation-policy.json"
            policy = json.loads(path.read_text(encoding="utf-8"))
            policy["machine_authority"]["publication_state"] = "README.md"
            write_json(path, policy)
            self.assertIn("publication machine authority", validate_machine_records.validate(root)[0])
        finally:
            temp.cleanup()

    def test_machine_priority_cannot_be_disabled(self):
        temp, root = self.fixture()
        try:
            path = root / "registry" / "representation-policy.json"
            policy = json.loads(path.read_text(encoding="utf-8"))
            policy["machine_priority"] = False
            write_json(path, policy)
            self.assertIn("machine_priority", validate_machine_records.validate(root)[0])
        finally:
            temp.cleanup()

    def test_publication_source_state_must_match_manifest(self):
        temp, root = self.fixture()
        try:
            path = root / "registry" / "publication-state.json"
            state = json.loads(path.read_text(encoding="utf-8"))
            state["editable_source"]["registry_version"] = "9.9.9"
            write_json(path, state)
            self.assertIn("drifted from manifest", validate_machine_records.validate(root)[0])
        finally:
            temp.cleanup()

    def test_trusted_release_cannot_be_draft(self):
        temp, root = self.fixture()
        try:
            path = root / "registry" / "publication-state.json"
            state = json.loads(path.read_text(encoding="utf-8"))
            state["trusted_release"]["draft"] = True
            write_json(path, state)
            self.assertIn("non-draft", validate_machine_records.validate(root)[0])
        finally:
            temp.cleanup()

    def test_trusted_release_must_be_immutable(self):
        temp, root = self.fixture()
        try:
            path = root / "registry" / "publication-state.json"
            state = json.loads(path.read_text(encoding="utf-8"))
            state["trusted_release"]["immutable"] = False
            write_json(path, state)
            self.assertIn("immutable", validate_machine_records.validate(root)[0])
        finally:
            temp.cleanup()

    def test_trusted_release_sequence_must_advance_source(self):
        temp, root = self.fixture()
        try:
            path = root / "registry" / "publication-state.json"
            state = json.loads(path.read_text(encoding="utf-8"))
            state["trusted_release"]["release_sequence"] = 0
            write_json(path, state)
            self.assertIn("greater than editable source", validate_machine_records.validate(root)[0])
        finally:
            temp.cleanup()

    def test_live_external_reverification_cannot_be_removed(self):
        temp, root = self.fixture()
        try:
            path = root / "registry" / "publication-state.json"
            state = json.loads(path.read_text(encoding="utf-8"))
            state["verification"]["external_reverification_required_before_trust_or_mutation"] = False
            write_json(path, state)
            self.assertIn("re-verification", validate_machine_records.validate(root)[0])
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
