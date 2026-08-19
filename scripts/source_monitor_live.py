from __future__ import annotations

import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse, urlunparse

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
EU_GDPR_CELLAR_URL = "https://publications.europa.eu/resource/celex/32016R0679?language=eng"
EU_CELLAR_AUTHORITY_DOMAIN = "publications.europa.eu"
EU_GDPR_TEXT_SENTINELS = (
    "REGULATION (EU) 2016/679",
    "Article 99",
)

_core_fetch = source_monitor._fetch


class _HttpsOnlyCellarRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        parsed = urlparse(newurl)
        if parsed.scheme == "http" and source_monitor._authorized_host(parsed.hostname, EU_CELLAR_AUTHORITY_DOMAIN):
            parsed = parsed._replace(scheme="https")
            newurl = urlunparse(parsed)
        parsed = urlparse(newurl)
        if parsed.scheme != "https" or not source_monitor._authorized_host(parsed.hostname, EU_CELLAR_AUTHORITY_DOMAIN):
            raise source_monitor.SourceMonitorError(
                f"official Cellar redirect left HTTPS publications.europa.eu boundary: {newurl}"
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _eu_cellar_fetch(source: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if config["strategy"] != "HTML_NORMALIZED_TEXT":
        raise source_monitor.SourceMonitorError(
            f"official Cellar XHTML monitor for {source['source_id']} must use HTML_NORMALIZED_TEXT"
        )
    request = urllib.request.Request(
        EU_GDPR_CELLAR_URL,
        headers={
            "Accept": "application/xhtml+xml",
            "Accept-Language": "eng",
            "Accept-Max-Cs-Size": str(config["max_bytes"]),
            "User-Agent": source_monitor.USER_AGENT,
        },
    )
    opener = urllib.request.build_opener(_HttpsOnlyCellarRedirectHandler())
    try:
        with opener.open(request, timeout=config["timeout_seconds"]) as response:
            raw = response.read(config["max_bytes"] + 1)
            if len(raw) > config["max_bytes"]:
                raise source_monitor.SourceMonitorError(f"source {source['source_id']} exceeds max_bytes")
            final_url = response.geturl()
            content_type = response.headers.get_content_type() or "application/octet-stream"
            charset = response.headers.get_content_charset() or "utf-8"
    except source_monitor.SourceMonitorError:
        raise
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise source_monitor.SourceMonitorError(
            f"official Cellar source fetch failed for {source['source_id']}: {exc}"
        ) from exc

    parsed = urlparse(final_url)
    if parsed.scheme != "https" or not source_monitor._authorized_host(parsed.hostname, EU_CELLAR_AUTHORITY_DOMAIN):
        raise source_monitor.SourceMonitorError(
            f"official Cellar source {source['source_id']} ended outside HTTPS publications.europa.eu boundary: {final_url}"
        )
    if content_type != "application/xhtml+xml":
        raise source_monitor.SourceMonitorError(
            f"official Cellar source {source['source_id']} returned unexpected content type {content_type}"
        )

    text = raw.decode(charset, errors="replace")
    normalized = source_monitor.normalize_html_text(text)
    if not normalized:
        raise source_monitor.SourceMonitorError(
            f"official Cellar source {source['source_id']} normalized text is empty"
        )
    missing_sentinels = [sentinel for sentinel in EU_GDPR_TEXT_SENTINELS if sentinel not in normalized]
    if missing_sentinels:
        raise source_monitor.SourceMonitorError(
            f"official Cellar source {source['source_id']} is missing expected GDPR text sentinels {missing_sentinels}"
        )

    return {
        "source_id": source["source_id"],
        "canonical_url": source["canonical_url"],
        "final_url": final_url,
        "strategy": config["strategy"],
        "content_type": content_type,
        "content_length": len(raw),
        "raw_sha256": source_monitor._sha256_bytes(raw),
        "normalized_text_sha256": source_monitor._sha256_bytes(normalized.encode("utf-8")),
        "fetched_at": source_monitor._now_iso(),
        "authority_boundary_ok": True,
    }


def _live_fetch(source: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if source["source_id"] == EU_GDPR_SOURCE_ID:
        return _eu_cellar_fetch(source, config)
    return _core_fetch(source, config)


source_monitor._fetch = _live_fetch


if __name__ == "__main__":
    raise SystemExit(source_monitor.main())
