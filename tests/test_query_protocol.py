from __future__ import annotations

import copy
import unittest

from scripts import query_protocol
from scripts.validate_schema_contracts import ContractError


class QueryProtocolTests(unittest.TestCase):
    def test_query_receipt_binds_editable_registry_and_result(self) -> None:
        receipt, result = query_protocol.build_receipt(
            "obligations",
            domain="privacy",
            jurisdiction="PH",
        )
        self.assertEqual("EDITABLE_REGISTRY_STATE", receipt["registry_authority_realm"])
        self.assertEqual("NOT_ESTABLISHED_BY_LOCAL_QUERY", receipt["publication_trust"])
        self.assertEqual(len(result), receipt["result_count"])
        self.assertTrue(receipt["external_reverification_required_before_trust_or_mutation"])
        self.assertTrue(receipt["promotion_from_receipt_forbidden"])
        self.assertRegex(receipt["manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(receipt["record_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(receipt["result_semantic_sha256"], r"^[0-9a-f]{64}$")

    def test_filter_change_changes_result_digest(self) -> None:
        unfiltered, _ = query_protocol.build_receipt("obligations")
        filtered, result = query_protocol.build_receipt("obligations", jurisdiction="US")
        self.assertEqual([], result)
        self.assertNotEqual(unfiltered["result_semantic_sha256"], filtered["result_semantic_sha256"])

    def test_receipt_cannot_claim_publication_trust(self) -> None:
        receipt, _ = query_protocol.build_receipt("sources")
        tampered = copy.deepcopy(receipt)
        tampered["publication_trust"] = "TRUSTED_RELEASE"
        with self.assertRaises(ContractError):
            query_protocol.validate_receipt(tampered)

    def test_receipt_cannot_become_authority(self) -> None:
        receipt, _ = query_protocol.build_receipt("sources")
        tampered = copy.deepcopy(receipt)
        tampered["authority"] = "CANONICAL"
        with self.assertRaises(ContractError):
            query_protocol.validate_receipt(tampered)


if __name__ == "__main__":
    unittest.main()
