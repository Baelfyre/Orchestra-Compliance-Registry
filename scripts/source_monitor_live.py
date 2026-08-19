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

# Some official publishers expose a canonical citation URL that is less stable for
# unattended clients than another official representation on the same authority
# domain. These overrides change only the monitor transport endpoint. They do not
# replace the Registry canonical citation URL or expand the trusted authority domain.
OFFICIAL_MONITOR_URL_OVERRIDES = {
    "EU-GDPR-2016-679": "https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32016R0679",
}

_core_fetch = source_monitor._fetch


def _live_fetch(source: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    original_canonical_url = source["canonical_url"]
    monitor_url = OFFICIAL_MONITOR_URL_OVERRIDES.get(source["source_id"])
    if monitor_url is None:
        return _core_fetch(source, config)
    monitor_source = dict(source)
    monitor_source["canonical_url"] = monitor_url
    result = _core_fetch(monitor_source, config)
    result["canonical_url"] = original_canonical_url
    return result


source_monitor._fetch = _live_fetch


if __name__ == "__main__":
    raise SystemExit(source_monitor.main())
