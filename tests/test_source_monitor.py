from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import source_monitor

ROOT = Path(__file__).resolve().parents[1]


class SourceMonitorTests(unittest.TestCase):
    def test_checked_in_monitor_config_covers_every_current_source(self) -> None:
        result = source_monitor.validate_config(
            ROOT,
            ROOT / "machine" / "source-monitor-policy.json",
            ROOT / "machine" / "source-monitor-baseline.v1.json",
        )
        self.assertEqual(result["source_count"], 8)
        self.assertEqual(result["configured_source_count"], 8)
        self.assertEqual(result["baseline_state"], "ACTIVE")
        self.assertEqual(result["baseline_source_count"], 8)

    def test_html_normalization_ignores_scripts_styles_and_whitespace(self) -> None:
        first = "<html><style>x{}</style><body><h1>Privacy Act</h1><script>dynamic()</script><p>Section 1</p></body></html>"
        second = "<html><body>  <h1>Privacy   Act</h1> <p>Section 1</p> </body></html>"
        self.assertEqual(source_monitor.normalize_html_text(first), source_monitor.normalize_html_text(second))

    def test_html_raw_change_with_same_normalized_text_is_metadata_only(self) -> None:
        previous = {
            "strategy": "HTML_NORMALIZED_TEXT",
            "raw_sha256": "a" * 64,
            "normalized_text_sha256": "b" * 64,
            "final_url": "https://example.gov/law",
        }
        current = {
            "strategy": "HTML_NORMALIZED_TEXT",
            "raw_sha256": "c" * 64,
            "normalized_text_sha256": "b" * 64,
            "final_url": "https://example.gov/law",
            "authority_boundary_ok": True,
        }
        state, _ = source_monitor.classify_fingerprint(previous, current)
        self.assertEqual(state, "METADATA_ONLY")

    def test_html_text_change_requires_human_interpretation_candidate(self) -> None:
        previous = {
            "strategy": "HTML_NORMALIZED_TEXT",
            "raw_sha256": "a" * 64,
            "normalized_text_sha256": "b" * 64,
            "final_url": "https://example.gov/law",
        }
        current = {
            "strategy": "HTML_NORMALIZED_TEXT",
            "raw_sha256": "c" * 64,
            "normalized_text_sha256": "d" * 64,
            "final_url": "https://example.gov/law",
            "authority_boundary_ok": True,
        }
        state, _ = source_monitor.classify_fingerprint(previous, current)
        self.assertEqual(state, "POTENTIAL_SUBSTANTIVE_CHANGE")

    def test_binary_digest_change_is_potential_substantive_change(self) -> None:
        previous = {
            "strategy": "BINARY_SHA256",
            "raw_sha256": "a" * 64,
            "normalized_text_sha256": None,
            "final_url": "https://example.gov/circular.pdf",
        }
        current = {
            "strategy": "BINARY_SHA256",
            "raw_sha256": "b" * 64,
            "normalized_text_sha256": None,
            "final_url": "https://example.gov/circular.pdf",
            "authority_boundary_ok": True,
        }
        state, _ = source_monitor.classify_fingerprint(previous, current)
        self.assertEqual(state, "POTENTIAL_SUBSTANTIVE_CHANGE")

    def test_authority_boundary_escape_is_source_moved(self) -> None:
        previous = {
            "strategy": "HTML_NORMALIZED_TEXT",
            "raw_sha256": "a" * 64,
            "normalized_text_sha256": "b" * 64,
            "final_url": "https://example.gov/law",
        }
        current = {
            "strategy": "HTML_NORMALIZED_TEXT",
            "raw_sha256": "a" * 64,
            "normalized_text_sha256": "b" * 64,
            "final_url": "https://example.com/law",
            "authority_boundary_ok": False,
        }
        state, _ = source_monitor.classify_fingerprint(previous, current)
        self.assertEqual(state, "SOURCE_MOVED")

    def test_candidate_application_marks_only_changed_source_for_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "registry").mkdir(parents=True)
            status_document = {
                "schema_version": 1,
                "entries": [
                    {
                        "source_id": "SRC-A",
                        "status": "VERIFIED_CURRENT",
                        "checked_at": "2026-08-19",
                        "check_method": "TEST",
                        "note": "unchanged",
                    },
                    {
                        "source_id": "SRC-B",
                        "status": "VERIFIED_CURRENT",
                        "checked_at": "2026-08-19",
                        "check_method": "TEST",
                        "note": "unchanged",
                    },
                ],
            }
            (root / "registry" / "source-status.json").write_text(
                json.dumps(status_document), encoding="utf-8"
            )
            receipt = {
                "$schema": "../schema/source-watch-receipt.schema.json",
                "schema_version": source_monitor.RECEIPT_SCHEMA_VERSION,
                "canonical_repository": source_monitor.CANONICAL_REPOSITORY,
                "checked_at": "2026-08-19T15:00:00Z",
                "baseline_captured_at": "2026-08-19T14:00:00Z",
                "overall_state": "CHANGES_DETECTED",
                "source_results": [
                    {
                        "source_id": "SRC-A",
                        "state": "POTENTIAL_SUBSTANTIVE_CHANGE",
                        "strategy": "HTML_NORMALIZED_TEXT",
                        "canonical_url": "https://example.gov/a",
                        "final_url": "https://example.gov/a",
                        "content_type": "text/html",
                        "previous_raw_sha256": "a" * 64,
                        "current_raw_sha256": "b" * 64,
                        "previous_normalized_text_sha256": "c" * 64,
                        "current_normalized_text_sha256": "d" * 64,
                        "reason": "normalized text changed",
                        "fetched_at": "2026-08-19T15:00:00Z",
                    },
                    {
                        "source_id": "SRC-B",
                        "state": "UNCHANGED",
                        "strategy": "HTML_NORMALIZED_TEXT",
                        "canonical_url": "https://example.gov/b",
                        "final_url": "https://example.gov/b",
                        "content_type": "text/html",
                        "previous_raw_sha256": "e" * 64,
                        "current_raw_sha256": "e" * 64,
                        "previous_normalized_text_sha256": "f" * 64,
                        "current_normalized_text_sha256": "f" * 64,
                        "reason": "unchanged",
                        "fetched_at": "2026-08-19T15:00:00Z",
                    },
                ],
                "actionable_source_ids": ["SRC-A"],
                "failure_source_ids": [],
                "candidate_key": "1" * 64,
                "observation_digest": "2" * 64,
            }
            receipt_path = root / "receipt.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            candidate_path = root / "machine" / "source-watch-candidate.json"

            source_monitor.apply_candidate(root, receipt_path, candidate_path)

            updated = json.loads((root / "registry" / "source-status.json").read_text(encoding="utf-8"))
            by_id = {item["source_id"]: item for item in updated["entries"]}
            self.assertEqual(by_id["SRC-A"]["status"], "HUMAN_INTERPRETATION_REQUIRED")
            self.assertEqual(by_id["SRC-B"]["status"], "VERIFIED_CURRENT")
            self.assertTrue(candidate_path.is_file())


if __name__ == "__main__":
    unittest.main()
