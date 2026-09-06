from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts import validate_registry

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 8, 14)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class RegistryValidatorTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(ROOT / "registry", root / "registry")
        return temp, root

    def set_single_source(
        self,
        root: Path,
        *,
        source_state: str = "VERIFIED_CURRENT",
        ledger_state: str | None = None,
        next_review_due: str = "2026-11-12",
    ) -> None:
        ledger_state = ledger_state or source_state
        write_json(
            root / "registry" / "sources.json",
            {
                "schema_version": 1,
                "sources": [
                    {
                        "source_id": "SRC-1",
                        "canonical_url": "https://example.com/source",
                        "jurisdiction_ids": ["PH"],
                        "domains": ["privacy"],
                        "verification": {"status": source_state},
                    }
                ],
            },
        )
        write_json(
            root / "registry" / "source-status.json",
            {"schema_version": 1, "entries": [{"source_id": "SRC-1", "status": ledger_state}]},
        )
        write_json(
            root / "registry" / "review-due.json",
            {"schema_version": 1, "entries": [{"source_id": "SRC-1", "next_review_due": next_review_due}]},
        )
        write_json(root / "registry" / "obligations.json", {"schema_version": 1, "obligations": []})
        manifest_path = root / "registry" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["record_counts"].update({"sources": 1, "obligations": 0, "source_status": 1, "review_due": 1})
        write_json(manifest_path, manifest)

    def write_source_watch_candidate(
        self,
        root: Path,
        *,
        result_state: str = "POTENTIAL_SUBSTANTIVE_CHANGE",
        source_id: str = "SRC-1",
    ) -> None:
        (root / "machine").mkdir(parents=True, exist_ok=True)
        write_json(
            root / "machine" / "source-watch-candidate.json",
            {
                "$schema": "../schema/source-watch-receipt.schema.json",
                "schema_version": validate_registry.SOURCE_WATCH_RECEIPT_SCHEMA_VERSION,
                "canonical_repository": validate_registry.CANONICAL_REPOSITORY,
                "checked_at": "2026-09-06T04:50:15Z",
                "baseline_captured_at": "2026-08-19T15:36:28Z",
                "overall_state": "CHANGES_DETECTED",
                "source_results": [
                    {
                        "source_id": source_id,
                        "state": result_state,
                        "strategy": "HTML_NORMALIZED_TEXT",
                        "canonical_url": "https://example.com/source",
                        "final_url": "https://example.com/source",
                        "content_type": "text/html",
                        "previous_raw_sha256": "a" * 64,
                        "current_raw_sha256": "b" * 64,
                        "previous_normalized_text_sha256": "c" * 64,
                        "current_normalized_text_sha256": "d" * 64,
                        "reason": "official source fingerprint changed",
                        "fetched_at": "2026-09-06T04:50:15Z",
                    }
                ],
                "actionable_source_ids": [source_id],
                "failure_source_ids": [],
                "candidate_key": "1" * 64,
                "observation_digest": "2" * 64,
            },
        )

    def test_repository_fixture_is_valid(self):
        self.assertEqual([], validate_registry.validate(ROOT, today=TODAY))

    def test_manifest_record_path_drift_is_rejected(self):
        temp, root = self.fixture()
        try:
            manifest_path = root / "registry" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["records"]["sources"] = "../outside.json"
            write_json(manifest_path, manifest)
            self.assertIn("records map", validate_registry.validate(root, today=TODAY)[0])
        finally:
            temp.cleanup()

    def test_unsafe_registry_version_is_rejected(self):
        temp, root = self.fixture()
        try:
            manifest_path = root / "registry" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["registry_version"] = "../escape"
            write_json(manifest_path, manifest)
            self.assertIn("safe version token", validate_registry.validate(root, today=TODAY)[0])
        finally:
            temp.cleanup()

    def test_source_status_must_reference_known_source(self):
        temp, root = self.fixture()
        try:
            path = root / "registry" / "source-status.json"
            write_json(path, {"schema_version": 1, "entries": [{"source_id": "SRC-MISSING", "status": "VERIFIED_CURRENT"}]})
            self.assertIn("unknown source", validate_registry.validate(root, today=TODAY)[0])
        finally:
            temp.cleanup()

    def test_review_due_requires_iso_date(self):
        temp, root = self.fixture()
        try:
            self.set_single_source(root, next_review_due="not-a-date")
            self.assertIn("invalid next_review_due", validate_registry.validate(root, today=TODAY)[0])
        finally:
            temp.cleanup()

    def test_draft_requires_source_status_coverage(self):
        temp, root = self.fixture()
        try:
            self.set_single_source(root)
            write_json(root / "registry" / "source-status.json", {"schema_version": 1, "entries": []})
            self.assertIn("source-status coverage mismatch", validate_registry.validate(root, today=TODAY)[0])
        finally:
            temp.cleanup()

    def test_draft_requires_review_due_coverage(self):
        temp, root = self.fixture()
        try:
            self.set_single_source(root)
            write_json(root / "registry" / "review-due.json", {"schema_version": 1, "entries": []})
            self.assertIn("review-due coverage mismatch", validate_registry.validate(root, today=TODAY)[0])
        finally:
            temp.cleanup()

    def test_source_and_status_ledger_must_agree(self):
        temp, root = self.fixture()
        try:
            self.set_single_source(root, source_state="VERIFIED_CURRENT", ledger_state="CURRENT_WITH_PENDING_CHANGE")
            self.assertIn("verification/status drift", validate_registry.validate(root, today=TODAY)[0])
        finally:
            temp.cleanup()

    def test_source_watch_candidate_mode_allows_receipt_backed_status_divergence(self):
        temp, root = self.fixture()
        try:
            self.set_single_source(
                root,
                source_state="VERIFIED_CURRENT",
                ledger_state="HUMAN_INTERPRETATION_REQUIRED",
            )
            self.write_source_watch_candidate(root)
            self.assertEqual(
                [],
                validate_registry.validate(
                    root,
                    today=TODAY,
                    allow_source_watch_candidate=True,
                ),
            )
        finally:
            temp.cleanup()

    def test_source_watch_candidate_file_does_not_weaken_default_validation(self):
        temp, root = self.fixture()
        try:
            self.set_single_source(
                root,
                source_state="VERIFIED_CURRENT",
                ledger_state="HUMAN_INTERPRETATION_REQUIRED",
            )
            self.write_source_watch_candidate(root)
            self.assertIn(
                "verification/status drift",
                validate_registry.validate(root, today=TODAY)[0],
            )
        finally:
            temp.cleanup()

    def test_source_watch_candidate_mode_rejects_unmatched_ledger_transition(self):
        temp, root = self.fixture()
        try:
            self.set_single_source(
                root,
                source_state="VERIFIED_CURRENT",
                ledger_state="HUMAN_INTERPRETATION_REQUIRED",
            )
            self.write_source_watch_candidate(root, result_state="SOURCE_MOVED")
            self.assertIn(
                "candidate/status drift",
                validate_registry.validate(
                    root,
                    today=TODAY,
                    allow_source_watch_candidate=True,
                )[0],
            )
        finally:
            temp.cleanup()

    def test_past_due_current_source_fails_closed(self):
        temp, root = self.fixture()
        try:
            self.set_single_source(root, next_review_due="2026-08-13")
            self.assertIn("review is overdue", validate_registry.validate(root, today=TODAY)[0])
        finally:
            temp.cleanup()

    def test_past_due_source_may_be_explicitly_marked_review_overdue(self):
        temp, root = self.fixture()
        try:
            self.set_single_source(
                root,
                source_state="REVIEW_OVERDUE",
                ledger_state="REVIEW_OVERDUE",
                next_review_due="2026-08-13",
            )
            self.assertEqual([], validate_registry.validate(root, today=TODAY))
        finally:
            temp.cleanup()

    def test_trusted_release_requires_positive_sequence(self):
        temp, root = self.fixture()
        try:
            manifest_path = root / "registry" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["status"] = "TRUSTED_RELEASE"
            manifest["release_sequence"] = 0
            write_json(manifest_path, manifest)
            self.assertIn("positive release_sequence", validate_registry.validate(root, today=TODAY)[0])
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
