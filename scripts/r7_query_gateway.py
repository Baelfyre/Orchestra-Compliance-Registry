#!/usr/bin/env python3
"""Deterministic R7 Registry read gateway.

Canonical ``registry/*.json`` remains authoritative. R7 adds provenance-bound typed
entities, deterministic relationships, a disposable verified SQLite index, bounded
projections, and one read-only query surface. It cannot mutate Registry state, infer
legal applicability, or publish a trusted release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts import context_export
    from scripts.validate_schema_contracts import validate_value
except ImportError:
    import context_export
    from validate_schema_contracts import validate_value

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "Baelfyre/Orchestra-Compliance-Registry"
INDEX_SCHEMA = "orchestra.compliance-registry.r7-index.v1"
RECEIPT_SCHEMA = "orchestra.compliance-registry.r7-query-receipt.v1"
PROJECTIONS = ("MINIMAL", "SUMMARY", "EVIDENCE", "FULL")
R7_CAPS = (
    "cap.query.v1", "cap.query.projection.v1", "cap.query.relationships.v1",
    "cap.query.indexed-read.v1", "cap.query.budget.v1",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

SOURCE_FIELDS = {
    "MINIMAL": ("source_id", "title", "jurisdiction_ids", "domains"),
    "SUMMARY": ("source_id", "title", "source_type", "authority", "jurisdiction_ids", "domains", "verification"),
    "EVIDENCE": ("source_id", "title", "source_type", "authority", "canonical_url", "citation", "jurisdiction_ids", "domains", "gathered_at", "verification", "interpretation_boundary"),
}
OBLIGATION_FIELDS = {
    "MINIMAL": ("obligation_id", "title", "jurisdiction_ids", "domains"),
    "SUMMARY": ("obligation_id", "title", "summary", "source_ids", "jurisdiction_ids", "provider_ids", "domains"),
    "EVIDENCE": ("obligation_id", "title", "summary", "source_ids", "jurisdiction_ids", "provider_ids", "domains", "source_locator", "required_evidence", "interpretation_state"),
}
ID_FIELD = {"sources": "source_id", "obligations": "obligation_id"}


class R7Error(ValueError):
    pass


class IndexIntegrityError(R7Error):
    pass


class ContextBudgetExceeded(R7Error):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R7Error(f"{path.as_posix()} must contain a JSON object")
    return value


@dataclass(frozen=True)
class EntityProvenance:
    record_path: str
    record_sha256: str
    entity_sha256: str


@dataclass(frozen=True)
class RegistrySource:
    source_id: str
    payload: dict[str, Any]
    provenance: EntityProvenance


@dataclass(frozen=True)
class RegistryObligation:
    obligation_id: str
    payload: dict[str, Any]
    provenance: EntityProvenance


@dataclass(frozen=True)
class RegistryJurisdiction:
    jurisdiction_id: str
    payload: dict[str, Any]
    provenance: EntityProvenance


@dataclass(frozen=True)
class RegistryProvider:
    provider_id: str
    payload: dict[str, Any]
    provenance: EntityProvenance


@dataclass(frozen=True)
class RegistrySourceStatus:
    source_id: str
    payload: dict[str, Any]
    provenance: EntityProvenance


@dataclass(frozen=True)
class RegistryReviewSchedule:
    source_id: str
    payload: dict[str, Any]
    provenance: EntityProvenance


@dataclass(frozen=True)
class RegistryCapability:
    capability_id: str
    payload: dict[str, Any]
    provenance: EntityProvenance


@dataclass(frozen=True)
class TypedRegistry:
    manifest: dict[str, Any]
    manifest_sha256: str
    collections: dict[str, dict[str, Any]]
    semantic_sha256: str


@dataclass(frozen=True)
class ReleaseIdentity:
    registry_version: str
    release_tag: str
    release_sequence: int
    release_manifest_sha256: str

    def validate(self) -> None:
        if not self.registry_version or not self.release_tag or self.release_sequence < 0:
            raise R7Error("invalid trusted release identity")
        if SHA256_RE.fullmatch(self.release_manifest_sha256) is None:
            raise R7Error("release_manifest_sha256 must be lowercase SHA-256")


@dataclass(frozen=True)
class QuerySpec:
    record_type: str
    domain: str | None = None
    jurisdiction: str | None = None
    provider: str | None = None
    source_id: str | None = None
    obligation_id: str | None = None
    projection: str = "SUMMARY"
    fields: tuple[str, ...] = ()
    include_freshness: bool = True
    limit: int = 50
    cursor: str | None = None
    maximum_context_bytes: int | None = None
    representation: str = "AUTO"

    def validate(self) -> None:
        if self.record_type not in ID_FIELD or self.projection not in PROJECTIONS:
            raise R7Error("unsupported record type or projection")
        if not 1 <= self.limit <= 1000:
            raise R7Error("limit must be between 1 and 1000")
        if self.maximum_context_bytes is not None and self.maximum_context_bytes <= 0:
            raise R7Error("maximum_context_bytes must be positive")
        if self.representation not in {"AUTO", "JSON", "TOON"}:
            raise R7Error("representation must be AUTO, JSON, or TOON")
        if len(self.fields) != len(set(self.fields)):
            raise R7Error("fields must be unique")


def _entities(root: Path, rel: str, key: str, id_key: str, cls: type) -> dict[str, Any]:
    path = root / rel
    rows = load_json(path).get(key)
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise R7Error(f"{rel}.{key} must be an array of objects")
    file_digest = digest(path.read_bytes())
    result: dict[str, Any] = {}
    for row in rows:
        entity_id = row.get(id_key)
        if not isinstance(entity_id, str) or not entity_id or entity_id in result:
            raise R7Error(f"invalid or duplicate {id_key}")
        result[entity_id] = cls(entity_id, row, EntityProvenance(rel, file_digest, digest(canonical(row))))
    return result


def load_typed_registry(root: Path = ROOT) -> TypedRegistry:
    manifest_path = root / "registry" / "manifest.json"
    manifest = load_json(manifest_path)
    if manifest.get("canonical_repository") != REPOSITORY or not isinstance(manifest.get("records"), dict):
        raise R7Error("Registry manifest identity mismatch")
    records = manifest["records"]
    definitions = {
        "sources": ("sources", "source_id", RegistrySource),
        "obligations": ("obligations", "obligation_id", RegistryObligation),
        "jurisdictions": ("jurisdictions", "jurisdiction_id", RegistryJurisdiction),
        "providers": ("providers", "provider_id", RegistryProvider),
        "source_status": ("entries", "source_id", RegistrySourceStatus),
        "review_due": ("entries", "source_id", RegistryReviewSchedule),
    }
    collections: dict[str, dict[str, Any]] = {}
    for name, (key, id_key, cls) in definitions.items():
        rel = records.get(name)
        if not isinstance(rel, str) or not rel.startswith("registry/"):
            raise R7Error(f"missing or unsafe record path for {name}")
        collections[name] = _entities(root, rel, key, id_key, cls)
    collections["capabilities"] = _entities(root, "registry/capabilities.json", "capabilities", "capability_id", RegistryCapability)
    if set(collections["sources"]) != set(collections["source_status"]) or set(collections["sources"]) != set(collections["review_due"]):
        raise R7Error("freshness ledgers must exactly cover source IDs")
    semantic = {name: [collections[name][item].payload for item in sorted(collections[name])] for name in sorted(collections)}
    semantic["manifest"] = manifest
    return TypedRegistry(manifest, digest(manifest_path.read_bytes()), collections, digest(canonical(semantic)))


def build_relationships(registry: TypedRegistry) -> dict[str, dict[str, tuple[str, ...]]]:
    c = registry.collections
    mutable: dict[str, dict[str, set[str]]] = {
        "source_obligation": {key: set() for key in c["sources"]},
        "obligation_source": {}, "source_jurisdiction": {}, "jurisdiction_source": {key: set() for key in c["jurisdictions"]},
        "obligation_jurisdiction": {}, "jurisdiction_obligation": {key: set() for key in c["jurisdictions"]},
        "obligation_provider": {}, "provider_obligation": {key: set() for key in c["providers"]},
        "source_domain": {}, "domain_source": {}, "obligation_domain": {}, "domain_obligation": {},
    }
    for source_id, entity in c["sources"].items():
        js, ds = set(entity.payload.get("jurisdiction_ids", [])), set(entity.payload.get("domains", []))
        mutable["source_jurisdiction"][source_id], mutable["source_domain"][source_id] = js, ds
        for j in js:
            if j not in c["jurisdictions"]:
                raise R7Error(f"unknown jurisdiction {j}")
            mutable["jurisdiction_source"][j].add(source_id)
        for d in ds:
            mutable["domain_source"].setdefault(d, set()).add(source_id)
    for oid, entity in c["obligations"].items():
        ss, js = set(entity.payload.get("source_ids", [])), set(entity.payload.get("jurisdiction_ids", []))
        ps, ds = set(entity.payload.get("provider_ids", [])), set(entity.payload.get("domains", []))
        mutable["obligation_source"][oid], mutable["obligation_jurisdiction"][oid] = ss, js
        mutable["obligation_provider"][oid], mutable["obligation_domain"][oid] = ps, ds
        for s in ss:
            if s not in c["sources"]:
                raise R7Error(f"unknown source {s}")
            mutable["source_obligation"][s].add(oid)
        for j in js:
            if j not in c["jurisdictions"]:
                raise R7Error(f"unknown jurisdiction {j}")
            mutable["jurisdiction_obligation"][j].add(oid)
        for p in ps:
            if p not in c["providers"]:
                raise R7Error(f"unknown provider {p}")
            mutable["provider_obligation"][p].add(oid)
        for d in ds:
            mutable["domain_obligation"].setdefault(d, set()).add(oid)
    result = {name: {key: tuple(sorted(values)) for key, values in sorted(mapping.items())} for name, mapping in sorted(mutable.items())}
    result["source_status"] = {key: (key,) for key in sorted(c["sources"])}
    result["source_review"] = {key: (key,) for key in sorted(c["sources"])}
    return result


def relationship_digest(relationships: dict[str, Any]) -> str:
    return digest(canonical(relationships))


def build_index(path: Path, identity: ReleaseIdentity, root: Path = ROOT) -> dict[str, str]:
    identity.validate()
    registry = load_typed_registry(root)
    relationships = build_relationships(registry)
    if registry.manifest.get("status") != "TRUSTED_RELEASE":
        raise R7Error("index requires TRUSTED_RELEASE Registry state")
    if registry.manifest.get("registry_version") != identity.registry_version or registry.manifest.get("release_sequence") != identity.release_sequence:
        raise R7Error("release identity does not match Registry manifest")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    meta = {
        "index_schema_version": INDEX_SCHEMA, "canonical_repository": REPOSITORY,
        "registry_version": identity.registry_version, "release_tag": identity.release_tag,
        "release_sequence": str(identity.release_sequence), "release_manifest_sha256": identity.release_manifest_sha256,
        "registry_manifest_sha256": registry.manifest_sha256, "registry_semantic_sha256": registry.semantic_sha256,
        "relationships_semantic_sha256": relationship_digest(relationships), "authority": "DERIVED_DISPOSABLE_READ_CACHE",
    }
    meta["index_semantic_sha256"] = digest(canonical({"registry": registry.semantic_sha256, "relationships": meta["relationships_semantic_sha256"]}))
    db = sqlite3.connect(path)
    try:
        db.executescript("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE records(record_type TEXT,entity_id TEXT,payload_json TEXT,PRIMARY KEY(record_type,entity_id)); CREATE TABLE relationships(relation_type TEXT,left_id TEXT,right_id TEXT,PRIMARY KEY(relation_type,left_id,right_id));")
        db.executemany("INSERT INTO meta VALUES(?,?)", sorted(meta.items()))
        rows = [(name, entity_id, canonical(entity.payload).decode()) for name, items in registry.collections.items() for entity_id, entity in sorted(items.items())]
        db.executemany("INSERT INTO records VALUES(?,?,?)", rows)
        rel_rows = [(name, left, right) for name, mapping in relationships.items() for left, rights in mapping.items() for right in rights]
        db.executemany("INSERT INTO relationships VALUES(?,?,?)", rel_rows)
        db.commit()
    finally:
        db.close()
    return verify_index(path, identity, root)


def _index_meta(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise IndexIntegrityError("index file does not exist")
    db = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        return dict(db.execute("SELECT key,value FROM meta ORDER BY key").fetchall())
    except sqlite3.DatabaseError as exc:
        raise IndexIntegrityError(str(exc)) from exc
    finally:
        db.close()


def verify_index(path: Path, identity: ReleaseIdentity, root: Path = ROOT) -> dict[str, str]:
    identity.validate()
    registry = load_typed_registry(root)
    relationships = build_relationships(registry)
    expected = {
        "index_schema_version": INDEX_SCHEMA, "canonical_repository": REPOSITORY,
        "registry_version": identity.registry_version, "release_tag": identity.release_tag,
        "release_sequence": str(identity.release_sequence), "release_manifest_sha256": identity.release_manifest_sha256,
        "registry_manifest_sha256": registry.manifest_sha256, "registry_semantic_sha256": registry.semantic_sha256,
        "relationships_semantic_sha256": relationship_digest(relationships), "authority": "DERIVED_DISPOSABLE_READ_CACHE",
    }
    expected["index_semantic_sha256"] = digest(canonical({"registry": registry.semantic_sha256, "relationships": expected["relationships_semantic_sha256"]}))
    actual = _index_meta(path)
    for key, value in expected.items():
        if actual.get(key) != value:
            raise IndexIntegrityError(f"index identity mismatch for {key}")
    return actual


def _index_records(path: Path, record_type: str) -> dict[str, dict[str, Any]]:
    db = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        rows = db.execute("SELECT entity_id,payload_json FROM records WHERE record_type=? ORDER BY entity_id", (record_type,)).fetchall()
    finally:
        db.close()
    return {key: json.loads(value) for key, value in rows}


def _freshness(source_id: str, registry: TypedRegistry) -> dict[str, Any]:
    c = registry.collections
    return {"source_id": source_id, "source_status": c["source_status"][source_id].payload, "review_schedule": c["review_due"][source_id].payload}


def _project(record_type: str, record: dict[str, Any], spec: QuerySpec, registry: TypedRegistry) -> dict[str, Any]:
    fields = tuple(record) if spec.projection == "FULL" else (SOURCE_FIELDS if record_type == "sources" else OBLIGATION_FIELDS)[spec.projection]
    if spec.fields:
        invalid = set(spec.fields) - set(fields)
        if invalid:
            raise R7Error(f"fields outside {spec.projection}: {sorted(invalid)}")
        identity = ID_FIELD[record_type]
        fields = tuple(key for key in fields if key == identity or key in spec.fields)
    result = {key: record[key] for key in fields if key in record}
    if spec.include_freshness:
        if record_type == "sources":
            result["_freshness"] = _freshness(record["source_id"], registry)
        else:
            result["_source_freshness"] = [_freshness(key, registry) for key in sorted(record.get("source_ids", []))]
    return result


def _query_model(spec: QuerySpec) -> dict[str, Any]:
    return {"record_type": spec.record_type, "filters": {"domain": spec.domain, "jurisdiction": spec.jurisdiction, "provider": spec.provider, "source_id": spec.source_id, "obligation_id": spec.obligation_id}, "projection": spec.projection, "fields": list(spec.fields), "include_freshness": spec.include_freshness, "limit": spec.limit, "cursor": spec.cursor, "maximum_context_bytes": spec.maximum_context_bytes}


def validate_r7_receipt(receipt: dict[str, Any], root: Path = ROOT) -> None:
    validate_value(receipt, load_json(root / "schema" / "r7-query-receipt.schema.json"), "r7_query_receipt")


def _encode(value: dict[str, Any], requested: str) -> tuple[str, bytes]:
    raw = canonical(value) + b"\n"
    toon = context_export.encode_toon(value).encode("utf-8")
    if requested == "JSON":
        return "JSON", raw
    if requested == "TOON":
        return "TOON", toon
    return ("TOON", toon) if len(toon) < len(raw) else ("JSON", raw)


class RegistryQueryGateway:
    def __init__(self, root: Path = ROOT, index_path: Path | None = None, release_identity: ReleaseIdentity | None = None):
        if (index_path is None) != (release_identity is None):
            raise R7Error("index_path and release_identity must be supplied together")
        self.root = root
        self.registry = load_typed_registry(root)
        self.relationships = build_relationships(self.registry)
        self.index_path = index_path
        self.release_identity = release_identity
        if index_path is not None and release_identity is not None:
            verify_index(index_path, release_identity, root)
            self.backend = "DIRECT_LOCAL_INDEXED_GATEWAY"
        else:
            self.backend = "DIRECT_LOCAL_JSON_QUERY"

    def _records(self, record_type: str) -> dict[str, dict[str, Any]]:
        if self.index_path is not None:
            return _index_records(self.index_path, record_type)
        return {key: entity.payload for key, entity in self.registry.collections[record_type].items()}

    def _filtered(self, spec: QuerySpec) -> list[dict[str, Any]]:
        rows = self._records(spec.record_type)
        out = []
        for entity_id, row in sorted(rows.items()):
            if spec.record_type == "sources":
                obligations = set(self.relationships["source_obligation"].get(entity_id, ()))
                checks = (
                    spec.source_id in (None, entity_id),
                    spec.domain is None or spec.domain in row.get("domains", []),
                    spec.jurisdiction is None or spec.jurisdiction in row.get("jurisdiction_ids", []),
                    spec.obligation_id is None or spec.obligation_id in obligations,
                    spec.provider is None or any(spec.provider in self.relationships["obligation_provider"].get(oid, ()) for oid in obligations),
                )
            else:
                checks = (
                    spec.obligation_id in (None, entity_id),
                    spec.source_id is None or spec.source_id in row.get("source_ids", []),
                    spec.domain is None or spec.domain in row.get("domains", []),
                    spec.jurisdiction is None or spec.jurisdiction in row.get("jurisdiction_ids", []),
                    spec.provider is None or spec.provider in row.get("provider_ids", []),
                )
            if all(checks):
                out.append(row)
        return out

    def query(self, spec: QuerySpec) -> dict[str, Any]:
        spec.validate()
        rows = self._filtered(spec)
        id_field = ID_FIELD[spec.record_type]
        start = 0
        if spec.cursor is not None:
            ids = [row[id_field] for row in rows]
            if spec.cursor not in ids:
                raise R7Error("cursor is not present in filtered results")
            start = ids.index(spec.cursor) + 1
        page = rows[start:start + spec.limit]
        more = start + len(page) < len(rows)
        next_cursor = page[-1][id_field] if more and page else None
        while True:
            projected = [_project(spec.record_type, row, spec, self.registry) for row in page]
            source_ids = sorted({row["source_id"] for row in page}) if spec.record_type == "sources" else sorted({sid for row in page for sid in row.get("source_ids", [])})
            obligation_ids = [] if spec.record_type == "sources" else sorted(row["obligation_id"] for row in page)
            identity = self.release_identity
            receipt = {
                "schema_version": RECEIPT_SCHEMA,
                "authority": "NONE_EVIDENCE_ONLY",
                "canonical_repository": REPOSITORY,
                "registry_authority_realm": "TRUSTED_RELEASE_READ_MODEL" if identity else "EDITABLE_REGISTRY_STATE",
                "publication_trust": "TRUSTED_RELEASE_IDENTITY_VERIFIED" if identity else "NOT_ESTABLISHED_BY_LOCAL_QUERY",
                "registry_version": identity.registry_version if identity else str(self.registry.manifest.get("registry_version")),
                "release_sequence": identity.release_sequence if identity else int(self.registry.manifest.get("release_sequence", 0)),
                "release_tag": identity.release_tag if identity else None,
                "release_manifest_sha256": identity.release_manifest_sha256 if identity else None,
                "registry_manifest_sha256": self.registry.manifest_sha256,
                "registry_semantic_sha256": self.registry.semantic_sha256,
                "relationship_semantic_sha256": relationship_digest(self.relationships),
                "backend": self.backend,
                "projection": spec.projection,
                "representation": "JSON",
                "query_semantic_sha256": digest(canonical(_query_model(spec))),
                "result_semantic_sha256": digest(canonical(projected)),
                "exact_source_ids": source_ids,
                "exact_obligation_ids": obligation_ids,
                "freshness_evidence": [_freshness(sid, self.registry) for sid in source_ids] if spec.include_freshness else [],
                "capability_negotiation_evidence": [
                    {
                        "capability_id": cap,
                        "contract_version": str(self.registry.collections["capabilities"][cap].payload.get("contract_version")),
                        "status": str(self.registry.collections["capabilities"][cap].payload.get("status")),
                    }
                    for cap in R7_CAPS if cap in self.registry.collections["capabilities"]
                ],
                "domain_routing_evidence": {
                    "requested_domain": spec.domain,
                    "returned_domains": sorted({d for row in page for d in row.get("domains", [])}),
                },
                "next_cursor": next_cursor,
                "integrity_disposition": "VERIFIED_INDEX" if self.index_path else "DIRECT_CANONICAL_JSON",
                "authority_expansion": False,
                "model_authored_integrity_repair": False,
                "external_reverification_required_before_trust_or_mutation": True,
                "promotion_from_receipt_forbidden": True,
            }
            response = {
                "schema_version": "orchestra.compliance-registry.r7-query-response.v1",
                "authority": "DERIVED_NON_AUTHORITATIVE",
                "backend": self.backend,
                "projection": spec.projection,
                "query": _query_model(spec),
                "total_filtered": len(rows),
                "count": len(projected),
                "next_cursor": next_cursor,
                "records": projected,
                "receipt": receipt,
            }
            representation, encoded = _encode(response, spec.representation)
            response["receipt"]["representation"] = representation
            representation, encoded = _encode(response, spec.representation)
            if spec.maximum_context_bytes is None or len(encoded) <= spec.maximum_context_bytes:
                validate_r7_receipt(response["receipt"], self.root)
                response["encoded_bytes"] = len(encoded)
                return response
            if len(page) <= 1:
                raise ContextBudgetExceeded("R7 response envelope exceeds maximum_context_bytes")
            page = page[:-1]
            next_cursor = page[-1][id_field]

    def relations(self, kind: str, entity_id: str) -> dict[str, Any]:
        maps = {
            "source": ("source_obligation", "source_jurisdiction", "source_domain"),
            "obligation": ("obligation_source", "obligation_jurisdiction", "obligation_provider", "obligation_domain"),
            "jurisdiction": ("jurisdiction_source", "jurisdiction_obligation"),
            "provider": ("provider_obligation",),
            "domain": ("domain_source", "domain_obligation"),
        }
        if kind not in maps:
            raise R7Error("unsupported relation entity type")
        values = {name: list(self.relationships[name].get(entity_id, ())) for name in maps[kind]}
        if not any(values.values()) and kind not in {"provider"}:
            raise KeyError(entity_id)
        return {"entity_type": kind, "entity_id": entity_id, "relations": values, "authority": "DERIVED_NON_AUTHORITATIVE"}

    def status(self) -> dict[str, Any]:
        return {
            "schema_version": "orchestra.compliance-registry.r7-status.v1",
            "authority": "DESCRIPTIVE_NON_AUTHORIZING",
            "backend": self.backend,
            "registry_version": self.registry.manifest.get("registry_version"),
            "release_sequence": self.registry.manifest.get("release_sequence"),
            "registry_manifest_sha256": self.registry.manifest_sha256,
            "registry_semantic_sha256": self.registry.semantic_sha256,
            "relationship_semantic_sha256": relationship_digest(self.relationships),
            "capabilities": [cap for cap in R7_CAPS if cap in self.registry.collections["capabilities"]],
            "authority_expansion": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R7 deterministic Registry read gateway")
    sub = parser.add_subparsers(dest="command", required=True)
    query = sub.add_parser("query")
    query.add_argument("record_type", choices=sorted(ID_FIELD))
    query.add_argument("--domain")
    query.add_argument("--jurisdiction")
    query.add_argument("--provider")
    query.add_argument("--source-id")
    query.add_argument("--obligation-id")
    query.add_argument("--projection", choices=PROJECTIONS, default="SUMMARY")
    query.add_argument("--field", action="append", default=[])
    query.add_argument("--without-freshness", action="store_true")
    query.add_argument("--limit", type=int, default=50)
    query.add_argument("--cursor")
    query.add_argument("--maximum-context-bytes", type=int)
    query.add_argument("--representation", choices=("AUTO", "JSON", "TOON"), default="AUTO")
    rel = sub.add_parser("relations")
    rel.add_argument("entity_type", choices=("source", "obligation", "jurisdiction", "provider", "domain"))
    rel.add_argument("entity_id")
    sub.add_parser("status")
    args = parser.parse_args(argv)
    gateway = RegistryQueryGateway()
    if args.command == "query":
        value = gateway.query(QuerySpec(args.record_type, args.domain, args.jurisdiction, args.provider, args.source_id, args.obligation_id, args.projection, tuple(args.field), not args.without_freshness, args.limit, args.cursor, args.maximum_context_bytes, args.representation))
    elif args.command == "relations":
        value = gateway.relations(args.entity_type, args.entity_id)
    else:
        value = gateway.status()
    print(json.dumps(value, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
