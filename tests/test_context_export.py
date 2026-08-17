from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.context_export import compile_export, encode_toon, filter_records, sha


class ContextExportTests(unittest.TestCase):
    def test_uniform_large_context_uses_toon_when_beneficial(self) -> None:
        context = {
            "schema_version": "fixture",
            "records": [
                {"id": f"O-{i:04d}", "jurisdiction": "PH", "severity": "HIGH", "status": "PENDING"}
                for i in range(1000)
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            manifest = compile_export(
                context,
                Path(tmp) / "context.compiled",
                Path(tmp) / "manifest.json",
                source_path="fixture.json",
                source_digest=sha(b"fixture"),
                min_bytes=100,
                min_savings_percent=1,
            )
            self.assertEqual(manifest["selected_format"], "TOON")
            self.assertTrue(manifest["promotion_from_projection_forbidden"])

    def test_small_nested_context_falls_back_to_json(self) -> None:
        context = {"records": [{"id": "A", "domains": ["privacy", "security"]}]}
        with tempfile.TemporaryDirectory() as tmp:
            manifest = compile_export(
                context,
                Path(tmp) / "context.compiled",
                Path(tmp) / "manifest.json",
                source_path="fixture.json",
                source_digest=sha(b"fixture"),
            )
            self.assertEqual(manifest["selected_format"], "JSON")

    def test_filter_preserves_only_requested_domain_and_jurisdiction(self) -> None:
        document = {
            "obligations": [
                {"obligation_id": "A", "domains": ["privacy"], "jurisdiction_ids": ["PH"]},
                {"obligation_id": "B", "domains": ["security"], "jurisdiction_ids": ["US"]},
            ]
        }
        result = filter_records(document, "obligations", "privacy", "PH")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["records"][0]["obligation_id"], "A")
        self.assertEqual(result["authority"], "DERIVED_NON_AUTHORITATIVE")

    def test_toon_table_declares_row_count(self) -> None:
        value = {"records": [{"id": i, "status": "PASS"} for i in range(25)]}
        self.assertIn("records[25]{id,status}:", encode_toon(value))


if __name__ == "__main__":
    unittest.main()
