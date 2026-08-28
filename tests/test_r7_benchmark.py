from __future__ import annotations

import unittest
from pathlib import Path

from scripts import r7_benchmark

ROOT = Path(__file__).resolve().parents[1]


class R7BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = r7_benchmark.run_benchmark(ROOT)
        cls.modes = {item["mode"]: item for item in cls.result["modes"]}

    def test_all_frozen_benchmark_modes_are_measured(self) -> None:
        self.assertEqual(
            {
                "RAW_REPOSITORY_CONTEXT",
                "CURRENT_FULL_JSON_QUERY",
                "CURRENT_JSON_TOON_EXPORT",
                "R7_PROJECTED_JSON",
                "R7_PROJECTED_TOON",
                "INDEXED_DIRECT_QUERY",
                "INDEXED_MCP_QUERY",
            },
            set(self.modes),
        )

    def test_benchmark_conformance_passes_without_authority_expansion(self) -> None:
        self.assertEqual("PASS", self.result["status"])
        conformance = self.result["conformance"]
        self.assertTrue(conformance["indexed_mcp_to_direct_payload_parity"])
        self.assertTrue(conformance["source_obligation_identity_parity"])
        self.assertTrue(conformance["all_r7_receipts_freshness_and_governance_correct"])
        self.assertFalse(conformance["authority_expansion"])

    def test_host_token_measurement_is_not_fabricated(self) -> None:
        for mode in self.result["modes"]:
            self.assertIsNone(mode["host_reported_input_tokens"])
            self.assertEqual("UNAVAILABLE_IN_LOCAL_DETERMINISTIC_BENCHMARK", mode["host_token_measurement_state"])
        evidence = self.result["efficiency_evidence"]
        self.assertFalse(evidence["token_efficiency_established"])
        self.assertEqual("HOST_REPORTED_INPUT_TOKENS_UNAVAILABLE", evidence["token_efficiency_reason"])

    def test_byte_efficiency_is_data_derived(self) -> None:
        evidence = self.result["efficiency_evidence"]
        baseline = evidence["full_json_output_bytes"]
        optimized = evidence["smallest_r7_projected_output_bytes"]
        expected = round(100.0 * (baseline - optimized) / max(1, baseline), 2)
        self.assertEqual(expected, evidence["measured_projected_savings_percent"])
        self.assertEqual(optimized < baseline, evidence["projected_byte_benefit_established"])


if __name__ == "__main__":
    unittest.main()
