from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DISALLOWED_CANONICAL_HOSTS = {
    "wikipedia.org",
    "www.wikipedia.org",
    "facebook.com",
    "www.facebook.com",
    "x.com",
    "twitter.com",
    "linkedin.com",
    "www.linkedin.com",
    "reddit.com",
    "www.reddit.com",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _host_matches_authority(host: str, authority_domain: str) -> bool:
    host = host.lower().rstrip(".")
    authority_domain = authority_domain.lower().rstrip(".")
    return host == authority_domain or host.endswith("." + authority_domain)


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    document = _load(root / "registry" / "sources.json")
    sources = document.get("sources", [])
    for source in sources:
        source_id = source.get("source_id", "<unknown>")
        canonical_url = source.get("canonical_url")
        citation = source.get("citation")
        verification = source.get("verification")
        gathered_at = source.get("gathered_at")

        if not isinstance(canonical_url, str):
            errors.append(f"{source_id}: canonical_url missing")
            continue
        parsed = urlparse(canonical_url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not host:
            errors.append(f"{source_id}: canonical source must use HTTPS")
        if host in DISALLOWED_CANONICAL_HOSTS:
            errors.append(f"{source_id}: canonical source host {host} is prohibited")

        if not isinstance(citation, dict):
            errors.append(f"{source_id}: structured official citation missing")
            continue
        if citation.get("primary_source") is not True or citation.get("official_source") is not True:
            errors.append(f"{source_id}: canonical citation must be an official primary source")
        if citation.get("official_url") != canonical_url:
            errors.append(f"{source_id}: citation official_url must equal canonical_url")

        authority_domain = verification.get("authority_domain") if isinstance(verification, dict) else None
        if not isinstance(authority_domain, str) or not _host_matches_authority(host, authority_domain):
            errors.append(
                f"{source_id}: canonical host {host!r} does not match recorded authority_domain {authority_domain!r}"
            )

        try:
            gathered = date.fromisoformat(gathered_at)
        except (TypeError, ValueError):
            errors.append(f"{source_id}: gathered_at must be an ISO date")
            continue
        verified_at = verification.get("verified_at") if isinstance(verification, dict) else None
        try:
            verified = date.fromisoformat(verified_at)
        except (TypeError, ValueError):
            errors.append(f"{source_id}: verification.verified_at must be an ISO date")
            continue
        if verified < gathered:
            errors.append(f"{source_id}: verified_at cannot precede gathered_at")

    return errors


def main() -> int:
    errors = validate(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("REGISTRY_SOURCE_PROVENANCE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
