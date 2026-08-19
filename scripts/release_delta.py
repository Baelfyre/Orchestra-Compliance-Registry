from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "orchestra.compliance-registry.release-delta.v1"
AUTHORITY = "EVIDENCE_ONLY_NON_AUTHORIZING"
COLLECTIONS: dict[str, tuple[str, str]] = {
    "capabilities": ("registry/capabilities.json", "capabilities"),
    "sources": ("registry/sources.json", "sources"),
    "obligations": ("registry/obligations.json", "obligations"),
    "jurisdictions": ("registry/jurisdictions.json", "jurisdictions"),
    "providers": ("registry/providers.json", "providers"),
    "source_status": ("registry/source-status.json", "entries"),
    "review_due": ("registry/review-due.json", "entries"),
}
ID_FIELDS = {
    "capabilities": "capability_id",
    "sources": "source_id",
    "obligations": "obligation_id",
    "jurisdictions": "jurisdiction_id",
    "providers": "provider_id",
    "source_status": "source_id",
    "review_due": "source_id",
}
HUMAN_REVIEW_STATES = {
    "HUMAN_INTERPRETATION_REQUIRED",
    "SOURCE_MOVED",
    "SOURCE_UNAVAILABLE",
    "REPEALED",
    "SUPERSEDED",
}


class DeltaError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeltaError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DeltaError(f"expected JSON object in {path}")
    return value


def manifest_identity(root: Path) -> dict[str, Any]:
    path = root / "registry" / "manifest.json"
    manifest = load_json(path)
    version = manifest.get("registry_version")
    sequence = manifest.get("release_sequence")
    if not isinstance(version, str) or not version:
        raise DeltaError("registry_version is missing")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        raise DeltaError("release_sequence is invalid")
    return {
        "registry_version": version,
        "release_sequence": sequence,
        "manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _collection(root: Path, name: str) -> dict[str, dict[str, Any]]:
    relative, key = COLLECTIONS[name]
    path = root / relative
    if not path.is_file():
        if name == "capabilities":
            return {}
        raise DeltaError(f"missing required record store: {relative}")
    document = load_json(path)
    values = document.get(key)
    if not isinstance(values, list) or not all(isinstance(item, dict) for item in values):
        raise DeltaError(f"{relative}.{key} must be an array of objects")
    id_field = ID_FIELDS[name]
    result: dict[str, dict[str, Any]] = {}
    for item in values:
        identity = item.get(id_field)
        if not isinstance(identity, str) or not identity:
            raise DeltaError(f"{relative} record missing {id_field}")
        if identity in result:
            raise DeltaError(f"{relative} contains duplicate {id_field} {identity}")
        result[identity] = item
    return result


def _changed_ids(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> tuple[set[str], set[str], set[str]]:
    before_ids = set(before)
    after_ids = set(after)
    added = after_ids - before_ids
    removed = before_ids - after_ids
    modified = {identity for identity in before_ids & after_ids if canonical(before[identity]) != canonical(after[identity])}
    return added, removed, modified


def _values(item: dict[str, Any], field: str) -> set[str]:
    value = item.get(field, [])
    if not isinstance(value, list):
        return set()
    return {entry for entry in value if isinstance(entry, str) and entry}


def _collect_impact(name: str, changed_ids: Iterable[str], before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]], affected: dict[str, set[str]]) -> None:
    for identity in changed_ids:
        for item in (before.get(identity), after.get(identity)):
            if not item:
                continue
            affected["domains"].update(_values(item, "domains"))
            affected["jurisdiction_ids"].update(_values(item, "jurisdiction_ids"))
            affected["provider_ids"].update(_values(item, "provider_ids"))
            if name in {"sources", "source_status", "review_due"}:
                source_id = item.get("source_id")
                if isinstance(source_id, str) and source_id:
                    affected["source_ids"].add(source_id)
            if name == "obligations":
                obligation_id = item.get("obligation_id")
                if isinstance(obligation_id, str) and obligation_id:
                    affected["obligation_ids"].add(obligation_id)
                affected["source_ids"].update(_values(item, "source_ids"))
            if name == "capabilities":
                capability_id = item.get("capability_id")
                if isinstance(capability_id, str) and capability_id:
                    affected["capability_ids"].add(capability_id)


def build_delta(base_root: Path, target_root: Path) -> dict[str, Any]:
    base_root = base_root.resolve()
    target_root = target_root.resolve()
    base_identity = manifest_identity(base_root)
    target_identity = manifest_identity(target_root)
    changed_record_types: list[str] = []
    structural_changes: set[str] = set()
    affected: dict[str, set[str]] = {
        "capability_ids": set(),
        "domains": set(),
        "jurisdiction_ids": set(),
        "provider_ids": set(),
        "source_ids": set(),
        "obligation_ids": set(),
    }
    capability_breaking = False
    human_review = False

    for name in COLLECTIONS:
        before = _collection(base_root, name)
        after = _collection(target_root, name)
        added, removed, modified = _changed_ids(before, after)
        changed = added | removed | modified
        if not changed:
            continue
        changed_record_types.append(name)
        _collect_impact(name, changed, before, after, affected)
        if added:
            structural_changes.add(f"{name}:ADDED")
        if removed:
            structural_changes.add(f"{name}:REMOVED")
        if modified:
            structural_changes.add(f"{name}:MODIFIED")
        if name == "capabilities":
            if removed:
                capability_breaking = True
            for identity in modified:
                old = before[identity]
                new = after[identity]
                if old.get("contract_version") != new.get("contract_version") or old.get("status") != new.get("status"):
                    capability_breaking = True
        if name in {"sources", "obligations"} and (removed or modified):
            human_review = True
        if name == "source_status":
            for identity in changed:
                candidate = after.get(identity, before.get(identity, {}))
                if candidate.get("status") in HUMAN_REVIEW_STATES:
                    human_review = True

    base_manifest = load_json(base_root / "registry" / "manifest.json")
    target_manifest = load_json(target_root / "registry" / "manifest.json")
    if base_manifest.get("records") != target_manifest.get("records"):
        structural_changes.add("MANIFEST_RECORD_MAP_CHANGED")

    if not changed_record_types and not structural_changes:
        disposition = "UNCHANGED"
    elif capability_breaking:
        disposition = "UNSUPPORTED_CAPABILITY_CHANGE"
    elif human_review:
        disposition = "HUMAN_REVIEW_REQUIRED"
    elif set(changed_record_types) & {"source_status", "review_due"}:
        disposition = "REVALIDATION_REQUIRED"
    else:
        disposition = "COMPATIBLE_SCOPED_CHANGE"

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "base": base_identity,
        "target": target_identity,
        "disposition": disposition,
        "changed_record_types": sorted(changed_record_types),
        "affected": {key: sorted(values) for key, values in affected.items()},
        "structural_changes": sorted(structural_changes),
        "requires_human_review": human_review,
    }
    result["digest"] = digest(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic Compliance Registry release/change delta.")
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = build_delta(args.base_root, args.target_root)
    except DeltaError as exc:
        print(f"RELEASE_DELTA_FAIL={exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
