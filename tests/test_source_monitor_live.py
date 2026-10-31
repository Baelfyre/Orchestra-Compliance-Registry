from __future__ import annotations

import unittest
from email.message import Message
from unittest.mock import patch

from scripts import source_monitor, source_monitor_live


class SourceMonitorLiveTests(unittest.TestCase):
    def test_official_cellar_http_identifier_is_upgraded_before_follow(self) -> None:
        url = "http://publications.europa.eu/resource/cellar/example/DOC_1"
        self.assertEqual(
            source_monitor_live._secure_cellar_redirect_url(url),
            "https://publications.europa.eu/resource/cellar/example/DOC_1",
        )

    def test_official_cellar_https_identifier_remains_https(self) -> None:
        url = "https://publications.europa.eu/resource/cellar/example/DOC_1"
        self.assertEqual(source_monitor_live._secure_cellar_redirect_url(url), url)

    def test_cellar_redirect_outside_official_https_boundary_fails_closed(self) -> None:
        with self.assertRaises(source_monitor.SourceMonitorError):
            source_monitor_live._secure_cellar_redirect_url(
                "https://example.com/resource/cellar/example/DOC_1"
            )

    def test_sso_current_date_boilerplate_does_not_change_normalized_digest_input(self) -> None:
        first = (
            "<html><body><h1>Personal Data Protection Act 2012</h1>"
            "<p>Current version as at 19 Aug 2026</p>"
            "<h2>DO NOT CALL REGISTRY</h2><p>Section 1</p></body></html>"
        )
        second = (
            "<html><body><h1>Personal Data Protection Act 2012</h1>"
            "<p>Current version as at 20 Aug 2026</p>"
            "<h2>DO NOT CALL REGISTRY</h2><p>Section 1</p></body></html>"
        )
        self.assertEqual(
            source_monitor_live._normalize_sg_pdpa_html(first),
            source_monitor_live._normalize_sg_pdpa_html(second),
        )

    def test_sso_legal_text_change_remains_detectable(self) -> None:
        first = (
            "<html><body><h1>Personal Data Protection Act 2012</h1>"
            "<p>Current version as at 20 Aug 2026</p>"
            "<h2>DO NOT CALL REGISTRY</h2><p>Section 1</p></body></html>"
        )
        second = (
            "<html><body><h1>Personal Data Protection Act 2012</h1>"
            "<p>Current version as at 20 Aug 2026</p>"
            "<h2>DO NOT CALL REGISTRY</h2><p>Section 1 amended</p></body></html>"
        )
        self.assertNotEqual(
            source_monitor_live._normalize_sg_pdpa_html(first),
            source_monitor_live._normalize_sg_pdpa_html(second),
        )

    def test_sso_missing_current_version_label_fails_closed(self) -> None:
        html = (
            "<html><body><h1>Personal Data Protection Act 2012</h1>"
            "<h2>DO NOT CALL REGISTRY</h2><p>Section 1</p></body></html>"
        )
        with self.assertRaises(source_monitor.SourceMonitorError):
            source_monitor_live._normalize_sg_pdpa_html(html)

    def test_sso_script_only_response_fails_with_bounded_diagnostics(self) -> None:
        html = b"<html><head><script>challenge()</script></head><body></body></html>"

        class ScriptOnlyResponse:
            status = 200

            def __init__(self) -> None:
                self.headers = Message()
                self.headers["Content-Type"] = "text/html; charset=utf-8"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self, limit):
                return html[:limit]

            def geturl(self):
                return "https://sso.agc.gov.sg/Act/PDPA2012"

        source = {
            "source_id": source_monitor_live.SG_PDPA_SOURCE_ID,
            "canonical_url": "https://sso.agc.gov.sg/Act/PDPA2012",
            "verification": {"authority_domain": "sso.agc.gov.sg"},
        }
        config = {"strategy": "HTML_NORMALIZED_TEXT", "timeout_seconds": 30, "max_bytes": 4096}
        with patch.object(source_monitor_live.urllib.request, "urlopen", return_value=ScriptOnlyResponse()):
            with self.assertRaises(source_monitor.SourceMonitorError) as failure:
                source_monitor_live._sg_pdpa_fetch(source, config)
        message = str(failure.exception)
        self.assertIn("normalized text is empty", message)
        self.assertIn("response_status=200", message)
        self.assertIn("content_type=text/html", message)
        self.assertIn(f"response_bytes={len(html)}", message)
        self.assertIn("raw_sha256=" + source_monitor._sha256_bytes(html), message)
        self.assertNotIn("challenge()", message)
        self.assertNotIn("<html>", message)

    def test_sso_invalid_legal_text_remains_untrusted(self) -> None:
        html = "<html><body><h1>Unverified text</h1></body></html>"
        with self.assertRaisesRegex(source_monitor.SourceMonitorError, "missing expected PDPA text sentinels"):
            source_monitor_live._normalize_sg_pdpa_html(html)


    def test_sso_http_202_is_rejected_before_text_normalization(self) -> None:
        html = b"<html><body><h1>Personal Data Protection Act 2012</h1></body></html>"

        class AcceptedResponse:
            status = 202

            def __init__(self):
                self.headers = Message()
                self.headers["Content-Type"] = "text/html; charset=utf-8"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self, limit):
                return html[:limit]

            def geturl(self):
                return "https://sso.agc.gov.sg/Act/PDPA2012"

        source = {
            "source_id": source_monitor_live.SG_PDPA_SOURCE_ID,
            "canonical_url": "https://sso.agc.gov.sg/Act/PDPA2012",
            "verification": {"authority_domain": "sso.agc.gov.sg"},
        }
        config = {"strategy": "HTML_NORMALIZED_TEXT", "timeout_seconds": 30, "max_bytes": 4096}
        with patch.object(source_monitor_live.urllib.request, "urlopen", return_value=AcceptedResponse()):
            with self.assertRaises(source_monitor.SourceMonitorError) as failure:
                source_monitor_live._sg_pdpa_fetch(source, config)
        self.assertIn("unexpected response_status=202", str(failure.exception))
        self.assertIn("raw_sha256=" + source_monitor._sha256_bytes(html), str(failure.exception))
        self.assertNotIn("<html>", str(failure.exception))



if __name__ == "__main__":
    unittest.main()
