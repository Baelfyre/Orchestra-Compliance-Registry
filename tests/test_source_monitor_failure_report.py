from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import source_monitor_failure_report as report


def receipt(failures=None, actionable=None, key="a" * 64, checked="2026-10-31T00:00:00Z"):
    return {
        "overall_state": "MONITOR_FAILURE",
        "failure_source_ids": ["SG-PDPA-2012"] if failures is None else failures,
        "actionable_source_ids": ["AU-PRIVACY-ACT-1988", "CA-PIPEDA-SC2000-C5"] if actionable is None else actionable,
        "candidate_key": key,
        "checked_at": checked,
    }


class FailureReportTests(unittest.TestCase):
    def test_signature_is_independent_of_run_timestamp_and_id_order(self) -> None:
        first = receipt()
        second = receipt(actionable=list(reversed(first["actionable_source_ids"])), checked="2026-11-01T00:00:00Z")
        self.assertEqual(report.failure_signature(first), report.failure_signature(second))

    def test_new_actionable_evidence_changes_signature(self) -> None:
        self.assertNotEqual(report.failure_signature(receipt()), report.failure_signature(receipt(actionable=[])))

    def test_repeated_classification_is_deduplicated(self) -> None:
        previous = report.render_report(receipt(), "https://github.com/Baelfyre/Orchestra-Compliance-Registry/actions/runs/1")
        self.assertTrue(report.already_reported(previous, receipt(checked="2026-11-01T00:00:00Z")))
        self.assertFalse(report.already_reported(previous, receipt(failures=["CA-PIPEDA-SC2000-C5"])))

    def test_report_records_actionable_sources_and_preserves_fail_closed_boundary(self) -> None:
        result = report.render_report(receipt(), "https://github.com/Baelfyre/Orchestra-Compliance-Registry/actions/runs/1")
        for expected in ("SG-PDPA-2012", "AU-PRIVACY-ACT-1988", "CA-PIPEDA-SC2000-C5",
                         "#artifacts", "no automated candidate", "trusted release"):
            self.assertIn(expected, result)

    def test_invalid_receipt_never_produces_report(self) -> None:
        with self.assertRaises(ValueError):
            report.failure_signature(receipt(failures=[]))
        with self.assertRaises(ValueError):
            report.render_report({**receipt(), "overall_state": "UNCHANGED"}, "https://github.com/example/1")

    def test_cli_dedup_creates_empty_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root / "receipt.json"
            previous = root / "previous.txt"
            output = root / "output.txt"
            payload.write_text(json.dumps(receipt()), encoding="utf-8")
            previous.write_text(report.render_report(receipt(), "https://github.com/a/b/actions/runs/1"), encoding="utf-8")
            from scripts.source_monitor_failure_report import main
            with patch("sys.argv", ["report", "--receipt", str(payload), "--previous-report", str(previous),
                                   "--output", str(output), "--run-url", "https://github.com/a/b/actions/runs/2"]):
                self.assertEqual(main(), 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "")

    def test_unknown_pre_receipt_failure_does_not_claim_artifact_exists(self) -> None:
        incomplete = receipt(failures=["UNKNOWN"], actionable=[], key=None)
        output = report.render_report(incomplete, "https://github.com/a/b/actions/runs/1")
        self.assertIn("Not generated; inspect the workflow logs", output)
        self.assertNotIn("#artifacts", output)
        self.assertEqual(report.failure_signature(incomplete), report.failure_signature(dict(incomplete)))



if __name__ == "__main__":
    unittest.main()
