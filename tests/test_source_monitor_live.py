from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
