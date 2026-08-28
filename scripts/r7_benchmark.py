#!/usr/bin/env python3
"""Measured R7 efficiency/conformance benchmark.

The benchmark records bytes and observed local latency for the seven surfaces frozen by
R7.9. It deliberately records host token counts as unavailable unless a host supplies
them. No efficiency claim is emitted from design intent alone.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import build_release, context_export, r7_mcp_server, r7_query_gateway, r7_trusted_release
except ImportError:
    import build_release  # type: ignore
    import context_export  # type: ignore
    import r7_mcp_server  # type: ignore
    import r7_query_gateway  # type: ignore
    import r7_trusted_release  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "orchestra.compliance-registry.r7-efficiency-benchmark.v1"
BENCHMARK_VERSION = "0.4.0-benchmark"
BENCHMARK_SEQUENCE = 4
BENCHMARK_TAG = f"registry-v{BENCHMARK_VERSION}"


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _measure(call: Callable[[], Any]) -> tuple[Any, int]:
    start = time.perf_counter_ns()
    value = call()
    return value, time.perf_counter_ns() - start


def _identity_from_records(records: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    source_ids = sorted({sid for row in records for sid in row.get("source_ids", []) if isinstance(sid, str)})
    obligation_ids = sorted({row["obligation_id"] for row in records if isinstance(row.get("obligation_id"), str)})
    return source_ids, obligation_ids


def _r7_checks(response: dict[str, Any]) -> dict[str, Any]:
    receipt = response.get("receipt")
    records = response.get("records")
    if not isinstance(receipt, dict) or not isinstance(records, list):
        return {"receipt_correct": False, "freshness_correct": False, "governance_correct": False}
    try:
        r7_query_gateway.validate_r7_receipt(receipt)
        receipt_correct = receipt.get("result_semantic_sha256") == r7_query_gateway.digest(r7_query_gateway.canonical(records))
    except Exception:
        receipt_correct = False
    source_ids, obligation_ids = _identity_from_records(records)
    freshness = receipt.get("freshness_evidence", [])
    freshness_ids = sorted(item.get("source_id") for item in freshness if isinstance(item, dict) and isinstance(item.get("source_id"), str))
    freshness_correct = source_ids == freshness_ids
    governance_correct = (
        receipt.get("authority") == "NONE_EVIDENCE_ONLY"
        and receipt.get("authority_expansion") is False
        and receipt.get("model_authored_integrity_repair") is False
        and receipt.get("promotion_from_receipt_forbidden") is True
        and response.get("authority") == "DERIVED_NON_AUTHORITATIVE"
    )
    return {
        "receipt_correct": receipt_correct,
        "freshness_correct": freshness_correct,
        "governance_correct": governance_correct,
        "source_ids": source_ids,
        "obligation_ids": obligation_ids,
        "records_returned": len(records),
    }


def _entry(
    name: str,
    *,
    input_bytes: int,
    output_bytes: int,
    latency_ns: int,
    tool_calls: int,
    files_scanned: int | None,
    records_scanned: int | None,
    records_returned: int,
    cache_state: str,
    source_ids: list[str],
    obligation_ids: list[str],
    receipt_correct: bool | None,
    freshness_correct: bool | None,
    governance_correct: bool,
) -> dict[str, Any]:
    return {
        "mode": name,
        "input_bytes": input_bytes,
        "output_bytes": output_bytes,
        "host_reported_input_tokens": None,
        "host_token_measurement_state": "UNAVAILABLE_IN_LOCAL_DETERMINISTIC_BENCHMARK",
        "tool_calls": tool_calls,
        "files_scanned": files_scanned,
        "records_scanned": records_scanned,
        "records_returned": records_returned,
        "latency_ns_observed": latency_ns,
        "latency_is_environment_dependent": True,
        "cache_state": cache_state,
        "source_ids": source_ids,
        "obligation_ids": obligation_ids,
        "receipt_correct": receipt_correct,
        "freshness_correct": freshness_correct,
        "governance_correct": governance_correct,
    }


def run_benchmark(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    direct_gateway = r7_query_gateway.RegistryQueryGateway(root=root)
    spec_full = r7_query_gateway.QuerySpec(
        record_type="obligations", domain="privacy", projection="FULL", limit=1000,
        representation="JSON",
    )
    spec_projected_json = r7_query_gateway.QuerySpec(
        record_type="obligations", domain="privacy", projection="EVIDENCE", limit=1000,
        representation="JSON",
    )
    spec_projected_toon = r7_query_gateway.QuerySpec(
        record_type="obligations", domain="privacy", projection="EVIDENCE", limit=1000,
        representation="TOON",
    )

    registry_paths = sorted((root / "registry").glob("*.json"))
    raw_bytes = sum(path.stat().st_size for path in registry_paths)
    raw_records = sum(len(items) for items in direct_gateway.registry.collections.values())

    full_response, full_latency = _measure(lambda: direct_gateway.query(spec_full))
    full_checks = _r7_checks(full_response)
    full_bytes = len(canonical(full_response)) + 1

    source_path, old_document = context_export.load_record("obligations")
    old_context = context_export.filter_records(old_document, "obligations", "privacy", None)
    old_json = canonical(old_context) + b"\n"
    old_toon = context_export.encode_toon(old_context).encode("utf-8")
    old_source_ids, old_obligation_ids = _identity_from_records(old_context["records"])

    projected_json, projected_json_latency = _measure(lambda: direct_gateway.query(spec_projected_json))
    projected_json_checks = _r7_checks(projected_json)
    projected_json_bytes = len(canonical(projected_json)) + 1

    projected_toon, projected_toon_latency = _measure(lambda: direct_gateway.query(spec_projected_toon))
    projected_toon_checks = _r7_checks(projected_toon)
    projected_toon_bytes = int(projected_toon["encoded_bytes"])

    entries: list[dict[str, Any]] = [
        _entry(
            "RAW_REPOSITORY_CONTEXT",
            input_bytes=raw_bytes, output_bytes=raw_bytes, latency_ns=0, tool_calls=0,
            files_scanned=len(registry_paths), records_scanned=raw_records,
            records_returned=raw_records, cache_state="NONE",
            source_ids=sorted(direct_gateway.registry.collections["sources"]),
            obligation_ids=sorted(direct_gateway.registry.collections["obligations"]),
            receipt_correct=None, freshness_correct=None, governance_correct=True,
        ),
        _entry(
            "CURRENT_FULL_JSON_QUERY",
            input_bytes=source_path.stat().st_size, output_bytes=full_bytes, latency_ns=full_latency,
            tool_calls=1, files_scanned=1, records_scanned=len(old_document.get("obligations", [])),
            records_returned=full_checks["records_returned"], cache_state="NONE",
            source_ids=full_checks["source_ids"], obligation_ids=full_checks["obligation_ids"],
            receipt_correct=full_checks["receipt_correct"], freshness_correct=full_checks["freshness_correct"],
            governance_correct=full_checks["governance_correct"],
        ),
        _entry(
            "CURRENT_JSON_TOON_EXPORT",
            input_bytes=source_path.stat().st_size, output_bytes=min(len(old_json), len(old_toon)), latency_ns=0,
            tool_calls=1, files_scanned=1, records_scanned=len(old_document.get("obligations", [])),
            records_returned=len(old_context["records"]), cache_state="NONE",
            source_ids=old_source_ids, obligation_ids=old_obligation_ids,
            receipt_correct=None, freshness_correct=None, governance_correct=True,
        ),
        _entry(
            "R7_PROJECTED_JSON",
            input_bytes=source_path.stat().st_size, output_bytes=projected_json_bytes, latency_ns=projected_json_latency,
            tool_calls=1, files_scanned=1, records_scanned=len(old_document.get("obligations", [])),
            records_returned=projected_json_checks["records_returned"], cache_state="DIRECT_JSON",
            source_ids=projected_json_checks["source_ids"], obligation_ids=projected_json_checks["obligation_ids"],
            receipt_correct=projected_json_checks["receipt_correct"], freshness_correct=projected_json_checks["freshness_correct"],
            governance_correct=projected_json_checks["governance_correct"],
        ),
        _entry(
            "R7_PROJECTED_TOON",
            input_bytes=source_path.stat().st_size, output_bytes=projected_toon_bytes, latency_ns=projected_toon_latency,
            tool_calls=1, files_scanned=1, records_scanned=len(old_document.get("obligations", [])),
            records_returned=projected_toon_checks["records_returned"], cache_state="DIRECT_JSON",
            source_ids=projected_toon_checks["source_ids"], obligation_ids=projected_toon_checks["obligation_ids"],
            receipt_correct=projected_toon_checks["receipt_correct"], freshness_correct=projected_toon_checks["freshness_correct"],
            governance_correct=projected_toon_checks["governance_correct"],
        ),
    ]

    with tempfile.TemporaryDirectory(prefix="registry-r7-benchmark-") as temp_name:
        temp = Path(temp_name)
        assets = temp / "assets"
        build_release.build_release(
            root, assets, registry_version=BENCHMARK_VERSION,
            release_sequence=BENCHMARK_SEQUENCE, release_tag=BENCHMARK_TAG,
        )
        installed = temp / "installed"
        verified, _ = r7_trusted_release.install_release(assets, installed)
        index_path = temp / "registry-r7.sqlite3"
        r7_trusted_release.build_verified_index(installed, index_path, verified.release_manifest_sha256)
        indexed_gateway = r7_query_gateway.RegistryQueryGateway(installed, index_path, verified.identity)

        indexed_response, indexed_latency = _measure(lambda: indexed_gateway.query(spec_projected_json))
        indexed_checks = _r7_checks(indexed_response)
        indexed_bytes = len(canonical(indexed_response)) + 1
        entries.append(_entry(
            "INDEXED_DIRECT_QUERY",
            input_bytes=index_path.stat().st_size, output_bytes=indexed_bytes, latency_ns=indexed_latency,
            tool_calls=1, files_scanned=0, records_scanned=None,
            records_returned=indexed_checks["records_returned"], cache_state="VERIFIED_TRUSTED_RELEASE_INDEX",
            source_ids=indexed_checks["source_ids"], obligation_ids=indexed_checks["obligation_ids"],
            receipt_correct=indexed_checks["receipt_correct"], freshness_correct=indexed_checks["freshness_correct"],
            governance_correct=indexed_checks["governance_correct"],
        ))

        adapter = r7_mcp_server.RegistryMcpAdapter(indexed_gateway)
        mcp_response, mcp_latency = _measure(lambda: adapter.registry_query(
            record_type="obligations", domain="privacy", projection="EVIDENCE", limit=1000, representation="JSON"
        ))
        mcp_core = {key: value for key, value in mcp_response.items() if key not in {"transport_adapter", "authority_expansion"}}
        mcp_checks = _r7_checks(mcp_response)
        mcp_bytes = len(canonical(mcp_response)) + 1
        entries.append(_entry(
            "INDEXED_MCP_QUERY",
            input_bytes=index_path.stat().st_size, output_bytes=mcp_bytes, latency_ns=mcp_latency,
            tool_calls=1, files_scanned=0, records_scanned=None,
            records_returned=mcp_checks["records_returned"], cache_state="VERIFIED_TRUSTED_RELEASE_INDEX",
            source_ids=mcp_checks["source_ids"], obligation_ids=mcp_checks["obligation_ids"],
            receipt_correct=mcp_checks["receipt_correct"], freshness_correct=mcp_checks["freshness_correct"],
            governance_correct=mcp_checks["governance_correct"],
        ))
        mcp_direct_parity = canonical(mcp_core) == canonical(indexed_response)

    by_name = {entry["mode"]: entry for entry in entries}
    baseline = by_name["CURRENT_FULL_JSON_QUERY"]["output_bytes"]
    optimized = min(by_name["R7_PROJECTED_JSON"]["output_bytes"], by_name["R7_PROJECTED_TOON"]["output_bytes"])
    savings_percent = round(100.0 * (baseline - optimized) / max(1, baseline), 2)
    identity_parity = (
        by_name["R7_PROJECTED_JSON"]["source_ids"] == by_name["INDEXED_DIRECT_QUERY"]["source_ids"] == by_name["INDEXED_MCP_QUERY"]["source_ids"]
        and by_name["R7_PROJECTED_JSON"]["obligation_ids"] == by_name["INDEXED_DIRECT_QUERY"]["obligation_ids"] == by_name["INDEXED_MCP_QUERY"]["obligation_ids"]
    )
    all_r7_correct = all(
        entry["receipt_correct"] is True and entry["freshness_correct"] is True and entry["governance_correct"] is True
        for entry in entries if entry["mode"].startswith("R7_") or entry["mode"].startswith("INDEXED_")
    )
    result = {
        "schema_version": SCHEMA,
        "authority": "EVIDENCE_ONLY_NON_AUTHORIZING",
        "canonical_repository": r7_query_gateway.REPOSITORY,
        "scenario": {"record_type": "obligations", "domain": "privacy", "projection": "EVIDENCE"},
        "measurement_policy": {
            "byte_measurement": "ACTUAL_UTF8_BYTES_OR_FILE_SIZE",
            "latency_measurement": "LOCAL_PERF_COUNTER_NS_SINGLE_OBSERVATION_ENVIRONMENT_DEPENDENT",
            "host_tokens": "NOT_FABRICATED_NULL_WHEN_UNAVAILABLE",
            "benefit_claim_requires_measured_evidence": True,
        },
        "modes": entries,
        "conformance": {
            "indexed_mcp_to_direct_payload_parity": mcp_direct_parity,
            "source_obligation_identity_parity": identity_parity,
            "all_r7_receipts_freshness_and_governance_correct": all_r7_correct,
            "authority_expansion": False,
        },
        "efficiency_evidence": {
            "full_json_output_bytes": baseline,
            "smallest_r7_projected_output_bytes": optimized,
            "measured_projected_savings_percent": savings_percent,
            "projected_byte_benefit_established": optimized < baseline,
            "token_efficiency_established": False,
            "token_efficiency_reason": "HOST_REPORTED_INPUT_TOKENS_UNAVAILABLE",
        },
    }
    result["status"] = "PASS" if mcp_direct_parity and identity_parity and all_r7_correct else "FAIL"
    result["digest"] = r7_query_gateway.digest(canonical(result))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure R7 direct/projection/index/MCP efficiency and parity")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_benchmark(args.root)
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if result["status"] == "PASS" else 1
    except Exception as exc:
        print(f"R7_BENCHMARK_FAIL={exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
