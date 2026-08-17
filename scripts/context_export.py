#!/usr/bin/env python3
"""Export bounded Compliance Registry context without changing Registry authority.

Registry JSON remains canonical. Large/repetitive query results may be projected to
TOON for AI context only when measured output is materially smaller; otherwise compact
JSON is retained. Every CLI export also emits a digest-bound, evidence-only query
receipt that cannot establish immutable-release trust.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts import query_protocol
except ImportError:
    import query_protocol

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
DEFAULT_MIN_BYTES = 4096
DEFAULT_MIN_SAVINGS_PERCENT = 10.0


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    text = str(value)
    if text == "" or text != text.strip() or re.search(r"[,:\[\]{}#\n\r\t]", text):
        return json.dumps(text, ensure_ascii=False)
    if text.lower() in {"true", "false", "null"} or re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", text):
        return json.dumps(text, ensure_ascii=False)
    return text


def table(values: list[Any]) -> tuple[list[str], list[dict[str, Any]]] | None:
    if not values or not all(isinstance(item, dict) for item in values):
        return None
    fields = list(values[0].keys())
    if not fields:
        return None
    for item in values:
        if list(item.keys()) != fields or not all(is_scalar(item[field]) for field in fields):
            return None
    return fields, values


def encode_toon(value: Any) -> str:
    lines: list[str] = []

    def emit(node: Any, indent: int, key: str | None = None) -> None:
        pad = " " * indent
        if is_scalar(node):
            lines.append(f"{pad}{key + ': ' if key is not None else ''}{scalar(node)}")
            return
        if isinstance(node, dict):
            if key is not None:
                lines.append(f"{pad}{key}:")
                indent += 2
            for child_key, child in node.items():
                emit(child, indent, str(child_key))
            return
        if isinstance(node, list):
            t = table(node)
            if t:
                fields, rows = t
                header = f"[{len(rows)}]{{{','.join(fields)}}}:"
                lines.append(f"{pad}{key + header if key is not None else header}")
                for row in rows:
                    lines.append(f"{' ' * (indent + 2)}{','.join(scalar(row[field]) for field in fields)}")
            elif all(is_scalar(item) for item in node):
                label = f"{key}[{len(node)}]: " if key is not None else f"[{len(node)}]: "
                lines.append(f"{pad}{label}{','.join(scalar(item) for item in node)}")
            else:
                label = f"{key}[{len(node)}]:" if key is not None else f"[{len(node)}]:"
                lines.append(f"{pad}{label}")
                for item in node:
                    if is_scalar(item):
                        lines.append(f"{' ' * (indent + 2)}- {scalar(item)}")
                    elif isinstance(item, dict):
                        first = True
                        for child_key, child in item.items():
                            marker = "- " if first else "  "
                            if is_scalar(child):
                                lines.append(f"{' ' * (indent + 2)}{marker}{child_key}: {scalar(child)}")
                            else:
                                lines.append(f"{' ' * (indent + 2)}{marker}{child_key}:")
                                emit(child, indent + 6)
                            first = False
                    else:
                        emit(item, indent + 4)
            return
        raise TypeError(type(node))

    emit(value, 0)
    return "\n".join(lines) + "\n"


def load_record(record_name: str) -> tuple[Path, dict[str, Any]]:
    manifest = json.loads((REGISTRY / "manifest.json").read_text(encoding="utf-8"))
    records = manifest.get("records", {})
    if record_name not in records:
        raise KeyError(record_name)
    path = ROOT / records[record_name]
    return path, json.loads(path.read_text(encoding="utf-8"))


def filter_records(
    document: dict[str, Any], record_name: str, domain: str | None, jurisdiction: str | None
) -> dict[str, Any]:
    values = list(document.get(record_name, []))
    if domain:
        values = [item for item in values if domain in item.get("domains", [])]
    if jurisdiction:
        values = [item for item in values if jurisdiction in item.get("jurisdiction_ids", [])]
    return {
        "schema_version": "orchestra.compliance-registry.context.v1",
        "authority": "DERIVED_NON_AUTHORITATIVE",
        "record_type": record_name,
        "filters": {"domain": domain, "jurisdiction": jurisdiction},
        "count": len(values),
        "records": values,
    }


def compile_export(
    value: Any,
    output: Path,
    manifest_path: Path,
    *,
    source_path: str,
    source_digest: str,
    min_bytes: int = DEFAULT_MIN_BYTES,
    min_savings_percent: float = DEFAULT_MIN_SAVINGS_PERCENT,
) -> dict[str, Any]:
    compact = canonical(value)
    toon = encode_toon(value).encode("utf-8")
    savings = 100.0 * (len(compact) - len(toon)) / max(1, len(compact))
    use_toon = len(compact) >= min_bytes and savings >= min_savings_percent
    selected_format = "TOON" if use_toon else "JSON"
    selected = toon if use_toon else compact + b"\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(selected)
    manifest = {
        "schema_version": "orchestra.compliance-registry.context-export-manifest.v1",
        "authority": "NONE_DERIVED_CONTEXT_ONLY",
        "canonical_source_format": "JSON",
        "source_path": source_path,
        "source_sha256": source_digest,
        "context_semantic_sha256": sha(compact),
        "projection_sha256": sha(selected),
        "selected_format": selected_format,
        "compact_json_bytes": len(compact),
        "toon_bytes": len(toon),
        "toon_savings_percent": round(savings, 2),
        "promotion_from_projection_forbidden": True,
        "fallback": "COMPACT_JSON",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def bind_query_receipt(
    manifest: dict[str, Any],
    manifest_path: Path,
    receipt_path: Path,
    receipt: dict[str, Any],
) -> dict[str, Any]:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest.update(
        {
            "registry_authority_realm": receipt["registry_authority_realm"],
            "publication_trust": receipt["publication_trust"],
            "registry_manifest_sha256": receipt["manifest_sha256"],
            "query_result_semantic_sha256": receipt["result_semantic_sha256"],
            "query_receipt_sha256": sha(receipt_path.read_bytes()),
            "external_reverification_required_before_trust_or_mutation": receipt[
                "external_reverification_required_before_trust_or_mutation"
            ],
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compliance Registry JSON/TOON context exporter")
    parser.add_argument(
        "record",
        choices=["sources", "obligations", "jurisdictions", "providers", "source_status", "review_due"],
    )
    parser.add_argument("--domain")
    parser.add_argument("--jurisdiction")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--min-bytes", type=int, default=DEFAULT_MIN_BYTES)
    parser.add_argument("--min-savings-percent", type=float, default=DEFAULT_MIN_SAVINGS_PERCENT)
    args = parser.parse_args(argv)

    source_path, document = load_record(args.record)
    context = filter_records(document, args.record, args.domain, args.jurisdiction)
    receipt, receipt_records = query_protocol.build_receipt(
        args.record,
        domain=args.domain,
        jurisdiction=args.jurisdiction,
    )
    if receipt_records != context["records"]:
        raise RuntimeError("query receipt/result mismatch")
    manifest = compile_export(
        context,
        args.output,
        args.manifest,
        source_path=source_path.relative_to(ROOT).as_posix(),
        source_digest=sha(source_path.read_bytes()),
        min_bytes=args.min_bytes,
        min_savings_percent=args.min_savings_percent,
    )
    receipt_path = args.receipt or args.manifest.with_name(args.manifest.name + ".query-receipt.json")
    manifest = bind_query_receipt(manifest, args.manifest, receipt_path, receipt)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
