from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CANONICAL_REPOSITORY = "Baelfyre/Orchestra-Compliance-Registry"
POLICY_SCHEMA_VERSION = "orchestra.compliance-registry.source-monitor-policy.v1"
BASELINE_SCHEMA_VERSION = "orchestra.compliance-registry.source-monitor-baseline.v1"
RECEIPT_SCHEMA_VERSION = "orchestra.compliance-registry.source-watch-receipt.v1"
BASELINE_SCHEMA_REF = "../schema/source-monitor-baseline.schema.json"
RECEIPT_SCHEMA_REF = "../schema/source-watch-receipt.schema.json"
USER_AGENT = "Orchestra-Compliance-Registry-Source-Monitor/1.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ACTIONABLE_STATES = {"POTENTIAL_SUBSTANTIVE_CHANGE", "SOURCE_MOVED"}
FAILURE_STATES = {"SOURCE_UNAVAILABLE"}


class SourceMonitorError(RuntimeError):
    pass


class _VisibleTextParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def text(self) -> str:
        return " ".join(self._parts)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceMonitorError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SourceMonitorError(f"expected JSON object in {path}")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256_bytes(encoded)


def normalize_html_text(value: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(value)
    parser.close()
    normalized = unicodedata.normalize("NFKC", parser.text())
    return " ".join(normalized.split())


def _authorized_host(host: str | None, authority_domain: str) -> bool:
    if not host:
        return False
    normalized_host = host.lower().rstrip(".")
    normalized_authority = authority_domain.lower().rstrip(".")
    return normalized_host == normalized_authority or normalized_host.endswith("." + normalized_authority)


def _validate_policy_and_sources(policy: dict[str, Any], sources_document: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if policy.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise SourceMonitorError("unsupported source monitor policy schema")
    if policy.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise SourceMonitorError("source monitor policy canonical_repository mismatch")
    if policy.get("monitoring_enabled") is not True:
        raise SourceMonitorError("source monitoring must be enabled")
    if policy.get("official_primary_only") is not True:
        raise SourceMonitorError("source monitor must remain official-primary-only")
    if policy.get("automatic_candidate_pull_request") is not True:
        raise SourceMonitorError("source monitor candidate PR automation must remain enabled")
    if policy.get("automatic_merge") is not False:
        raise SourceMonitorError("source monitor must never auto-merge")
    if policy.get("automatic_trusted_release") is not False:
        raise SourceMonitorError("source monitor must never auto-publish a trusted release")
    if policy.get("human_interpretation_required_for_substantive_change") is not True:
        raise SourceMonitorError("substantive source changes must require human interpretation")

    sources = sources_document.get("sources")
    configs = policy.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
        raise SourceMonitorError("registry/sources.json must contain a sources array")
    if not isinstance(configs, list) or not all(isinstance(item, dict) for item in configs):
        raise SourceMonitorError("source monitor policy must contain a sources array")

    source_by_id: dict[str, dict[str, Any]] = {}
    for source in sources:
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise SourceMonitorError("source record has invalid source_id")
        if source_id in source_by_id:
            raise SourceMonitorError(f"duplicate source_id {source_id}")
        citation = source.get("citation")
        verification = source.get("verification")
        if not isinstance(citation, dict) or citation.get("primary_source") is not True or citation.get("official_source") is not True:
            raise SourceMonitorError(f"source {source_id} is not marked official primary")
        if not isinstance(verification, dict) or not isinstance(verification.get("authority_domain"), str):
            raise SourceMonitorError(f"source {source_id} lacks authority_domain")
        canonical_url = source.get("canonical_url")
        if not isinstance(canonical_url, str) or urlparse(canonical_url).scheme != "https":
            raise SourceMonitorError(f"source {source_id} must use HTTPS canonical_url")
        if not _authorized_host(urlparse(canonical_url).hostname, verification["authority_domain"]):
            raise SourceMonitorError(f"source {source_id} canonical_url is outside authority_domain")
        source_by_id[source_id] = source

    config_ids: set[str] = set()
    enabled_configs: list[dict[str, Any]] = []
    for config in configs:
        source_id = config.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise SourceMonitorError("monitor config has invalid source_id")
        if source_id in config_ids:
            raise SourceMonitorError(f"duplicate monitor config for {source_id}")
        config_ids.add(source_id)
        if source_id not in source_by_id:
            raise SourceMonitorError(f"monitor config references unknown source {source_id}")
        if config.get("enabled") is not True:
            raise SourceMonitorError(f"monitor config for {source_id} must remain enabled")
        if config.get("strategy") not in {"HTML_NORMALIZED_TEXT", "BINARY_SHA256"}:
            raise SourceMonitorError(f"unsupported monitor strategy for {source_id}")
        timeout = config.get("timeout_seconds")
        max_bytes = config.get("max_bytes")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
            raise SourceMonitorError(f"invalid timeout_seconds for {source_id}")
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
            raise SourceMonitorError(f"invalid max_bytes for {source_id}")
        enabled_configs.append(config)

    if config_ids != set(source_by_id):
        missing = sorted(set(source_by_id) - config_ids)
        extra = sorted(config_ids - set(source_by_id))
        raise SourceMonitorError(f"source monitor coverage mismatch missing={missing} extra={extra}")
    return enabled_configs, source_by_id


def validate_config(root: Path, policy_path: Path, baseline_path: Path | None = None) -> dict[str, Any]:
    policy = _load_json(policy_path)
    sources_document = _load_json(root / "registry" / "sources.json")
    configs, source_by_id = _validate_policy_and_sources(policy, sources_document)
    result: dict[str, Any] = {
        "canonical_repository": CANONICAL_REPOSITORY,
        "policy_schema_version": POLICY_SCHEMA_VERSION,
        "source_count": len(source_by_id),
        "configured_source_count": len(configs),
    }
    if baseline_path is not None:
        baseline = _load_json(baseline_path)
        state = baseline.get("baseline_state")
        if baseline.get("schema_version") != BASELINE_SCHEMA_VERSION:
            raise SourceMonitorError("unsupported source monitor baseline schema")
        if baseline.get("canonical_repository") != CANONICAL_REPOSITORY:
            raise SourceMonitorError("source monitor baseline canonical_repository mismatch")
        if state not in {"BOOTSTRAP_REQUIRED", "ACTIVE"}:
            raise SourceMonitorError("invalid source monitor baseline_state")
        fingerprints = baseline.get("source_fingerprints")
        if not isinstance(fingerprints, list) or not all(isinstance(item, dict) for item in fingerprints):
            raise SourceMonitorError("source monitor baseline fingerprints must be an array")
        ids = [item.get("source_id") for item in fingerprints]
        if len(ids) != len(set(ids)):
            raise SourceMonitorError("source monitor baseline contains duplicate source IDs")
        if state == "ACTIVE":
            if set(ids) != set(source_by_id):
                raise SourceMonitorError("ACTIVE source monitor baseline must cover every canonical source exactly once")
            for fingerprint in fingerprints:
                raw_sha = fingerprint.get("raw_sha256")
                normalized_sha = fingerprint.get("normalized_text_sha256")
                if not isinstance(raw_sha, str) or SHA256_RE.fullmatch(raw_sha) is None:
                    raise SourceMonitorError(f"invalid baseline raw_sha256 for {fingerprint.get('source_id')}")
                if normalized_sha is not None and (not isinstance(normalized_sha, str) or SHA256_RE.fullmatch(normalized_sha) is None):
                    raise SourceMonitorError(f"invalid baseline normalized_text_sha256 for {fingerprint.get('source_id')}")
        elif fingerprints:
            raise SourceMonitorError("BOOTSTRAP_REQUIRED baseline must not contain fingerprints")
        result["baseline_state"] = state
        result["baseline_source_count"] = len(fingerprints)
    return result


def _fetch(source: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    source_id = source["source_id"]
    canonical_url = source["canonical_url"]
    authority_domain = source["verification"]["authority_domain"]
    request = urllib.request.Request(
        canonical_url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=config["timeout_seconds"]) as response:
            raw = response.read(config["max_bytes"] + 1)
            if len(raw) > config["max_bytes"]:
                raise SourceMonitorError(f"source {source_id} exceeds max_bytes")
            final_url = response.geturl()
            content_type = response.headers.get_content_type() or "application/octet-stream"
            charset = response.headers.get_content_charset() or "utf-8"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SourceMonitorError(f"source fetch failed for {source_id}: {exc}") from exc

    if urlparse(final_url).scheme != "https" or not _authorized_host(urlparse(final_url).hostname, authority_domain):
        return {
            "source_id": source_id,
            "canonical_url": canonical_url,
            "final_url": final_url,
            "strategy": config["strategy"],
            "content_type": content_type,
            "content_length": len(raw),
            "raw_sha256": _sha256_bytes(raw),
            "normalized_text_sha256": None,
            "fetched_at": _now_iso(),
            "authority_boundary_ok": False,
        }

    normalized_sha: str | None = None
    if config["strategy"] == "HTML_NORMALIZED_TEXT":
        text = raw.decode(charset, errors="replace")
        normalized = normalize_html_text(text)
        if not normalized:
            raise SourceMonitorError(f"source {source_id} normalized HTML text is empty")
        normalized_sha = _sha256_bytes(normalized.encode("utf-8"))

    return {
        "source_id": source_id,
        "canonical_url": canonical_url,
        "final_url": final_url,
        "strategy": config["strategy"],
        "content_type": content_type,
        "content_length": len(raw),
        "raw_sha256": _sha256_bytes(raw),
        "normalized_text_sha256": normalized_sha,
        "fetched_at": _now_iso(),
        "authority_boundary_ok": True,
    }


def bootstrap(root: Path, policy_path: Path, output_path: Path) -> dict[str, Any]:
    policy = _load_json(policy_path)
    sources_document = _load_json(root / "registry" / "sources.json")
    configs, source_by_id = _validate_policy_and_sources(policy, sources_document)
    fingerprints = []
    for config in sorted(configs, key=lambda item: item["source_id"]):
        fingerprint = _fetch(source_by_id[config["source_id"]], config)
        if fingerprint["authority_boundary_ok"] is not True:
            raise SourceMonitorError(f"source {config['source_id']} redirected outside its official authority boundary")
        fingerprint.pop("authority_boundary_ok", None)
        fingerprints.append(fingerprint)
    payload = {
        "$schema": BASELINE_SCHEMA_REF,
        "schema_version": BASELINE_SCHEMA_VERSION,
        "canonical_repository": CANONICAL_REPOSITORY,
        "baseline_state": "ACTIVE",
        "captured_at": _now_iso(),
        "source_fingerprints": fingerprints,
    }
    _write_json(output_path, payload)
    return payload


def _baseline_by_id(baseline: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fingerprints = baseline.get("source_fingerprints")
    if not isinstance(fingerprints, list):
        raise SourceMonitorError("baseline source_fingerprints must be an array")
    result: dict[str, dict[str, Any]] = {}
    for item in fingerprints:
        if not isinstance(item, dict) or not isinstance(item.get("source_id"), str):
            raise SourceMonitorError("baseline fingerprint is malformed")
        if item["source_id"] in result:
            raise SourceMonitorError(f"duplicate baseline source {item['source_id']}")
        result[item["source_id"]] = item
    return result


def classify_fingerprint(previous: dict[str, Any], current: dict[str, Any]) -> tuple[str, str]:
    if current.get("authority_boundary_ok") is not True:
        return "SOURCE_MOVED", "final URL left the declared official authority domain"
    strategy = current.get("strategy")
    if strategy != previous.get("strategy"):
        return "POTENTIAL_SUBSTANTIVE_CHANGE", "monitor strategy changed and requires a new reviewed baseline"
    if strategy == "BINARY_SHA256":
        if current.get("raw_sha256") == previous.get("raw_sha256"):
            return "UNCHANGED", "binary digest unchanged"
        return "POTENTIAL_SUBSTANTIVE_CHANGE", "binary digest changed"
    if strategy == "HTML_NORMALIZED_TEXT":
        if current.get("normalized_text_sha256") != previous.get("normalized_text_sha256"):
            return "POTENTIAL_SUBSTANTIVE_CHANGE", "normalized official text digest changed"
        if current.get("raw_sha256") != previous.get("raw_sha256") or current.get("final_url") != previous.get("final_url"):
            return "METADATA_ONLY", "raw representation or same-authority URL changed while normalized text remained stable"
        return "UNCHANGED", "normalized and raw digests unchanged"
    raise SourceMonitorError(f"unsupported strategy {strategy!r}")


def check(root: Path, policy_path: Path, baseline_path: Path, receipt_path: Path) -> dict[str, Any]:
    validate_config(root, policy_path, baseline_path)
    policy = _load_json(policy_path)
    baseline = _load_json(baseline_path)
    if baseline.get("baseline_state") != "ACTIVE":
        raise SourceMonitorError("source monitor check requires an ACTIVE reviewed baseline")
    sources_document = _load_json(root / "registry" / "sources.json")
    configs, source_by_id = _validate_policy_and_sources(policy, sources_document)
    previous_by_id = _baseline_by_id(baseline)

    results: list[dict[str, Any]] = []
    for config in sorted(configs, key=lambda item: item["source_id"]):
        source_id = config["source_id"]
        previous = previous_by_id[source_id]
        try:
            current = _fetch(source_by_id[source_id], config)
            state, reason = classify_fingerprint(previous, current)
            results.append(
                {
                    "source_id": source_id,
                    "state": state,
                    "strategy": config["strategy"],
                    "canonical_url": source_by_id[source_id]["canonical_url"],
                    "final_url": current.get("final_url"),
                    "content_type": current.get("content_type"),
                    "previous_raw_sha256": previous.get("raw_sha256"),
                    "current_raw_sha256": current.get("raw_sha256"),
                    "previous_normalized_text_sha256": previous.get("normalized_text_sha256"),
                    "current_normalized_text_sha256": current.get("normalized_text_sha256"),
                    "reason": reason,
                    "fetched_at": current.get("fetched_at"),
                }
            )
        except SourceMonitorError as exc:
            results.append(
                {
                    "source_id": source_id,
                    "state": "SOURCE_UNAVAILABLE",
                    "strategy": config["strategy"],
                    "canonical_url": source_by_id[source_id]["canonical_url"],
                    "final_url": None,
                    "content_type": None,
                    "previous_raw_sha256": previous.get("raw_sha256"),
                    "current_raw_sha256": None,
                    "previous_normalized_text_sha256": previous.get("normalized_text_sha256"),
                    "current_normalized_text_sha256": None,
                    "reason": str(exc),
                    "fetched_at": None,
                }
            )

    actionable = sorted(item["source_id"] for item in results if item["state"] in ACTIONABLE_STATES)
    failures = sorted(item["source_id"] for item in results if item["state"] in FAILURE_STATES)
    if failures:
        overall_state = "MONITOR_FAILURE"
    elif actionable:
        overall_state = "CHANGES_DETECTED"
    else:
        overall_state = "UNCHANGED"

    candidate_identity = [
        {
            "source_id": item["source_id"],
            "state": item["state"],
            "final_url": item["final_url"],
            "current_raw_sha256": item["current_raw_sha256"],
            "current_normalized_text_sha256": item["current_normalized_text_sha256"],
        }
        for item in results
        if item["state"] in ACTIONABLE_STATES
    ]
    candidate_key = _sha256_json(candidate_identity) if candidate_identity else None
    checked_at = _now_iso()
    observation_core = {
        "checked_at": checked_at,
        "baseline_captured_at": baseline.get("captured_at"),
        "overall_state": overall_state,
        "source_results": results,
        "actionable_source_ids": actionable,
        "failure_source_ids": failures,
        "candidate_key": candidate_key,
    }
    payload = {
        "$schema": RECEIPT_SCHEMA_REF,
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "canonical_repository": CANONICAL_REPOSITORY,
        **observation_core,
        "observation_digest": _sha256_json(observation_core),
    }
    _write_json(receipt_path, payload)
    return payload


def apply_candidate(root: Path, receipt_path: Path, candidate_output: Path) -> dict[str, Any]:
    receipt = _load_json(receipt_path)
    if receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        raise SourceMonitorError("unsupported source-watch receipt schema")
    if receipt.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise SourceMonitorError("source-watch receipt canonical_repository mismatch")
    if receipt.get("overall_state") != "CHANGES_DETECTED":
        raise SourceMonitorError("candidate application requires CHANGES_DETECTED receipt")
    actionable_ids = receipt.get("actionable_source_ids")
    if not isinstance(actionable_ids, list) or not actionable_ids:
        raise SourceMonitorError("candidate receipt has no actionable sources")

    result_by_id = {
        item["source_id"]: item
        for item in receipt.get("source_results", [])
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }
    status_path = root / "registry" / "source-status.json"
    status_document = _load_json(status_path)
    entries = status_document.get("entries")
    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        raise SourceMonitorError("registry/source-status.json entries are malformed")
    status_by_id = {item.get("source_id"): item for item in entries}

    for source_id in actionable_ids:
        if source_id not in status_by_id or source_id not in result_by_id:
            raise SourceMonitorError(f"candidate references unknown source {source_id}")
        result = result_by_id[source_id]
        if result["state"] == "SOURCE_MOVED":
            status = "SOURCE_MOVED"
        elif result["state"] == "POTENTIAL_SUBSTANTIVE_CHANGE":
            status = "HUMAN_INTERPRETATION_REQUIRED"
        else:
            raise SourceMonitorError(f"unsupported actionable state {result['state']}")
        status_by_id[source_id].update(
            {
                "status": status,
                "checked_at": _today_iso(),
                "check_method": "AUTOMATED_OFFICIAL_SOURCE_CHANGE_DETECTION_REQUIRES_HUMAN_REVIEW",
                "note": (
                    f"Automated source monitor detected {result['state']} against the reviewed source baseline. "
                    "This candidate status is fail-closed evidence only; a human/Governor review must verify the official text, "
                    "date semantics, applicability, obligation impact, and any required baseline update before merge or trusted publication."
                ),
            }
        )

    status_document["entries"] = sorted(entries, key=lambda item: item["source_id"])
    _write_json(status_path, status_document)
    _write_json(candidate_output, receipt)
    return {
        "candidate_key": receipt.get("candidate_key"),
        "actionable_source_ids": actionable_ids,
        "source_status_path": status_path.as_posix(),
        "candidate_receipt_path": candidate_output.as_posix(),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor authoritative Registry sources without granting legal or publication authority.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-config")
    validate_parser.add_argument("--policy", default="machine/source-monitor-policy.json")
    validate_parser.add_argument("--baseline", default="machine/source-monitor-baseline.v1.json")

    bootstrap_parser = subparsers.add_parser("bootstrap")
    bootstrap_parser.add_argument("--policy", default="machine/source-monitor-policy.json")
    bootstrap_parser.add_argument("--output", required=True)

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--policy", default="machine/source-monitor-policy.json")
    check_parser.add_argument("--baseline", default="machine/source-monitor-baseline.v1.json")
    check_parser.add_argument("--receipt-output", required=True)

    apply_parser = subparsers.add_parser("apply-candidate")
    apply_parser.add_argument("--receipt", required=True)
    apply_parser.add_argument("--candidate-output", default="machine/source-watch-candidate.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == "validate-config":
            result = validate_config(root, root / args.policy, root / args.baseline)
            print("SOURCE_MONITOR_CONFIG_VALID=" + json.dumps(result, sort_keys=True))
            return 0
        if args.command == "bootstrap":
            payload = bootstrap(root, root / args.policy, Path(args.output).resolve())
            print("SOURCE_MONITOR_BOOTSTRAP_PASS=" + json.dumps({"source_count": len(payload["source_fingerprints"]), "captured_at": payload["captured_at"]}, sort_keys=True))
            return 0
        if args.command == "check":
            payload = check(root, root / args.policy, root / args.baseline, Path(args.receipt_output).resolve())
            print("SOURCE_MONITOR_CHECK=" + json.dumps({"overall_state": payload["overall_state"], "actionable_source_ids": payload["actionable_source_ids"], "failure_source_ids": payload["failure_source_ids"], "candidate_key": payload["candidate_key"]}, sort_keys=True))
            return 2 if payload["overall_state"] == "MONITOR_FAILURE" else 0
        if args.command == "apply-candidate":
            result = apply_candidate(root, Path(args.receipt).resolve(), root / args.candidate_output)
            print("SOURCE_MONITOR_CANDIDATE_APPLIED=" + json.dumps(result, sort_keys=True))
            return 0
        raise SourceMonitorError(f"unsupported command {args.command}")
    except SourceMonitorError as exc:
        print(f"SOURCE_MONITOR_FAIL={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
