from __future__ import annotations

from typing import Any

try:
    from scripts import source_monitor
except ImportError:  # direct script execution from repository root
    import source_monitor  # type: ignore


source_monitor.USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/139.0 Safari/537.36 "
    "OrchestraComplianceRegistryMonitor/1.0"
)

EU_GDPR_SOURCE_ID = "EU-GDPR-2016-679"
EU_GDPR_PDF_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32016R0679"

_core_fetch = source_monitor._fetch


def _live_fetch(source: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if source["source_id"] != EU_GDPR_SOURCE_ID:
        return _core_fetch(source, config)
    original_canonical_url = source["canonical_url"]
    monitor_source = dict(source)
    monitor_source["canonical_url"] = EU_GDPR_PDF_URL
    result = _core_fetch(monitor_source, config)
    result["canonical_url"] = original_canonical_url
    if result["authority_boundary_ok"] is True and result["content_type"] != "application/pdf":
        raise source_monitor.SourceMonitorError(
            f"official EUR-Lex PDF monitor for {source['source_id']} returned unexpected content type {result['content_type']}"
        )
    return result


source_monitor._fetch = _live_fetch


if __name__ == "__main__":
    raise SystemExit(source_monitor.main())
