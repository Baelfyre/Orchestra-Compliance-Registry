# R7 — Token-Efficient Registry Read Architecture

## Status

`APPROVED_PLANNED_NOT_IMPLEMENTED`

R7 is the approved post-measurement Registry optimization program. It must not begin runtime implementation until the current Orchestra Codex baseline program and Orchestra v1.7.0 closeout are complete.

## Objective

Reduce model/IDE context cost and repeated file parsing without changing Registry authority. Canonical `registry/*.json` records remain the source of truth. R7 adds a deterministic, disposable read model and bounded query gateway that can return only the exact Registry slice a consumer needs.

## Architecture

```text
canonical Registry JSON
        |
        | validate + hash
        v
typed entity mapping
        |
        v
derived relationship/index model
        |
        +--> direct local query
        +--> CLI adapter
        `--> read-only MCP adapter
                |
                v
        compact JSON / TOON projection
```

Authority boundary:

```text
canonical JSON = Registry authority
SQLite/index = derived disposable cache
query gateway = deterministic read layer
MCP = transport only
AI output = non-authoritative interpretation/projection
```

## Frozen compatibility rule

R7 is additive. Existing `cap.query.v1` remains the required compatibility floor. Existing R1-R6 records, source-monitor behavior, freshness semantics, release-delta semantics, and authority boundaries remain valid.

Proposed optional capabilities:

- `cap.query.projection.v1`
- `cap.query.relationships.v1`
- `cap.query.indexed-read.v1`
- `cap.query.budget.v1`
- `cap.transport.mcp.v1`

## Phase plan

### R7.0 — Contract freeze

Freeze entity, relationship, index, projection, query-budget, cache, MCP, fallback, and measurement contracts before implementation.

### R7.1 — Typed entity model

Map canonical records to deterministic typed entities:

- `RegistrySource`
- `RegistryObligation`
- `RegistryJurisdiction`
- `RegistryProvider`
- `RegistrySourceStatus`
- `RegistryReviewSchedule`
- `RegistryCapability`

Typed objects must retain canonical IDs and digest-bound provenance. They do not become authority.

### R7.2 — Relationship model

Derive explicit read relationships from existing IDs:

- Source <-> Obligation
- Source <-> Jurisdiction
- Obligation <-> Jurisdiction
- Obligation <-> Provider
- Source <-> Domain
- Obligation <-> Domain
- Source -> SourceStatus
- Source -> ReviewSchedule

No canonical record rewrite is required.

### R7.3 — Deterministic read index

Build a disposable local SQLite read model from verified Registry JSON. The index must bind to release tag, release sequence, release-manifest SHA-256, index schema version, and a deterministic semantic digest.

Any identity mismatch invalidates the cache and requires rebuild or fail-closed fallback.

### R7.4 — Projection contracts

Freeze four standard projections:

- `MINIMAL` — IDs, title, jurisdiction/domain classification for discovery.
- `SUMMARY` — minimal fields plus summary, source IDs, and freshness.
- `EVIDENCE` — summary plus source locator, required evidence, source status, review state, and citation identity.
- `FULL` — complete canonical records only when explicitly required.

### R7.5 — Query planner and context budget

Support deterministic filters and bounded responses using jurisdiction, provider, domain, source ID, obligation ID, field projection, detail level, limit/cursor, freshness inclusion, and maximum context bytes.

The planner must project first, then choose compact JSON or TOON. TOON remains derived and may only be selected when measured savings exist.

### R7.6 — Shared query gateway

Create one deterministic query core used by direct local calls, CLI, and MCP. This becomes the single implementation of Registry selection semantics and prevents consumer-side query drift.

### R7.7 — Read-only MCP adapter

Expose a deliberately small read-only surface:

- `registry_status`
- `registry_query`
- `registry_get`
- `registry_relations`
- `registry_freshness`
- `registry_delta`

The MCP adapter cannot mutate Registry records, publish releases, infer legal applicability, or expand authority.

### R7.8 — Trusted-release cache integration

Normal consumers should verify an immutable trusted Registry release, install the canonical JSON bundle, then build the derived read index locally. The index is rebuildable and is not a replacement for the trusted release.

### R7.9 — Efficiency benchmark

Compare:

1. raw repository context;
2. current full JSON query;
3. current JSON/TOON export;
4. R7 projected JSON;
5. R7 projected TOON;
6. indexed direct query;
7. indexed MCP query.

Measure input bytes, host-reported input tokens where available, tool calls, files/records scanned, records returned, latency, cache state, source/obligation coverage, receipt correctness, freshness correctness, and governance correctness.

Token-efficiency benefit must be evidence-derived; it must not be claimed from design intent alone.

## Completion gate

R7 is complete only when:

- canonical JSON authority is unchanged;
- all existing Registry validations remain green;
- v0.3 compatibility remains green;
- index rebuild is deterministic;
- index-to-JSON semantic parity passes;
- projection parity passes;
- query receipt parity passes;
- MCP-to-direct-query parity passes;
- authority expansion remains false;
- efficiency evidence is recorded.

## Planned release boundary

The intended feature release is `registry-v0.4.0`, after R7 implementation and joint R7/O7 conformance validation. Release publication remains a separate governed transition.

## Cross-repository dependency

Orchestra consumes R7 through a separate optional O7 phase. R7 must preserve the existing `cap.query.v1` contract so current Orchestra O1-O6 remains compatible while O7 is absent.

See the Orchestra plan: `docs/architecture/REGISTRY_QUERY_OPTIMIZATION_O7.md` in `Baelfyre/Orchestra`.
