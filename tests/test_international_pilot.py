from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InternationalPrivacyPilotTests(unittest.TestCase):
    def _load(self, relative: str) -> dict:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_source_backed_jurisdictions_have_sources_and_obligations(self) -> None:
        jurisdictions = self._load("registry/jurisdictions.json")["jurisdictions"]
        sources = self._load("registry/sources.json")["sources"]
        obligations = self._load("registry/obligations.json")["obligations"]

        expected_source_backed = {"PH", "EU-EEA", "CA", "AU", "SG"}
        actual_source_backed = {
            item["jurisdiction_id"]
            for item in jurisdictions
            if item["status"] == "SOURCE_BACKED_PILOT"
        }
        self.assertEqual(expected_source_backed, actual_source_backed)

        source_jurisdictions = {
            jurisdiction_id
            for source in sources
            for jurisdiction_id in source["jurisdiction_ids"]
        }
        obligation_jurisdictions = {
            jurisdiction_id
            for obligation in obligations
            for jurisdiction_id in obligation["jurisdiction_ids"]
        }

        for jurisdiction_id in expected_source_backed:
            self.assertIn(jurisdiction_id, source_jurisdictions)
            self.assertIn(jurisdiction_id, obligation_jurisdictions)

    def test_foundation_only_jurisdictions_are_not_presented_as_source_backed(self) -> None:
        jurisdictions = self._load("registry/jurisdictions.json")["jurisdictions"]
        by_id = {item["jurisdiction_id"]: item for item in jurisdictions}

        self.assertEqual("FOUNDATION_ONLY", by_id["US"]["status"])
        self.assertEqual("FOUNDATION_ONLY", by_id["MX"]["status"])

    def test_every_obligation_jurisdiction_is_registered(self) -> None:
        jurisdictions = self._load("registry/jurisdictions.json")["jurisdictions"]
        obligations = self._load("registry/obligations.json")["obligations"]
        known = {item["jurisdiction_id"] for item in jurisdictions}

        for obligation in obligations:
            for jurisdiction_id in obligation["jurisdiction_ids"]:
                self.assertIn(jurisdiction_id, known, obligation["obligation_id"])

    def test_international_sources_have_freshness_records(self) -> None:
        sources = self._load("registry/sources.json")["sources"]
        statuses = self._load("registry/source-status.json")["entries"]
        review_due = self._load("registry/review-due.json")["entries"]

        source_ids = {item["source_id"] for item in sources}
        status_ids = {item["source_id"] for item in statuses}
        review_ids = {item["source_id"] for item in review_due}

        self.assertEqual(source_ids, status_ids)
        self.assertEqual(source_ids, review_ids)


if __name__ == "__main__":
    unittest.main()
