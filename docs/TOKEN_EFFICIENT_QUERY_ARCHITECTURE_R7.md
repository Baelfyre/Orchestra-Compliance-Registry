# R7 — Token-Efficient Registry Read Architecture

## Status

`IMPLEMENTED_R7_1_R7_9_PENDING_TRUSTED_PUBLICATION_AND_O7_7_CONFORMANCE`

R7.1 through R7.6 are implemented as the stable, read-only direct query surface defined by this architecture. Canonical `registry/*.json` records remain the source of truth. The implementation adds deterministic typed entities, derived relationships, a disposable trusted-release SQLite index, bounded projections, context-budget enforcement, and a shared direct query gateway.

`IMPLEMENTED_READ_ONLY_TRANSPORT`

R7.7 read-only MCP transport, R7.8 trusted-release verification/cache installation, and R7.9 evidence-based efficiency benchmarking are implemented on the candidate surface. Trusted `registry-v0.4.0` publication and final Orchestra O7.7 conformance remain separate governed transitions and are not claimed by source implementation alone.

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

Stable optional direct-surface capabilities implemented at contract version `1.0.0`:

- `cap.query.projection.v1`
- `cap.query.relationships.v1`
- `cap.query.indexed-read.v1`
- `cap.query.budget.v1`

Additional optional transport capability implemented at contract version `1.0.0`:

- `cap.transport.mcp.v1`

## Implemented direct-surface contract

Machine state is recorded in `machine/r7-surface.v1.json` and validated by `schema/r7-surface.schema.json`, `schema/r7-query-receipt.schema.json`, `scripts/validate_r7_surface.py`, and `tests/test_r7_query_gateway.py`.

The stable direct surface is implemented in `scripts/r7_query_gateway.py` and provides:

- provenance-bound typed entities retaining canonical IDs and record/entity digests;
- deterministic source, obligation, jurisdiction, provider, domain, freshness, and review relationships;
- a disposable SQLite read index that can only be built against an explicitly supplied `TRUSTED_RELEASE` identity;
- `MINIMAL`, `SUMMARY`, `EVIDENCE`, and `FULL` projections;
- deterministic domain, jurisdiction, provider, source, and obligation filtering;
- bounded limit/cursor behavior and `maximum_context_bytes` fail-closed enforcement;
- compact JSON or TOON representation selection, with TOON selected only when smaller;
- direct JSON fallback when no verified index is supplied;
- evidence-only R7 receipts preserving exact source and obligation identities, freshness evidence, capability evidence, domain-routing evidence, semantic digests, and authority boundaries.

The Orchestra O7 entry token `IMPLEMENTED_STABLE_REGISTRY_R7_SURFACE_REQUIRED` is satisfied for O7.1 through O7.6 runtime implementation only. It does not satisfy the future trusted-release integration boundary and does not authorize or imply MCP transport.

## Phase plan

### R7.0 — Contract freeze

`COMPLETE`

Freeze entity, relationship, index, projection, query-budget, cache, MCP, fallback, and measurement contracts before implementation.

### R7.1 — Typed entity model

`IMPLEMENTED_STABLE`

Map canonical records to deterministic typed entities:

- `RegistrySource`
- `RegistryObligation`
- `RegistryJurisdiction`
- `RegistryProvider`
- `RegistrySourceStatus`
- `RegistryReviewSchedule`
- `RegistryCapability`

Typed objects retain canonical IDs and digest-bound provenance. They do not become authority.

### R7.2 — Relationship model

`IMPLEMENTED_STABLE`

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

`IMPLEMENTED_STABLE`

Build a disposable local SQLite read model from verified Registry JSON. The index binds to release tag, release sequence, release-manifest SHA-256, index schema version, Registry manifest identity, Registry semantic digest, and relationship semantic digest.

Any identity mismatch invalidates the cache and requires rebuild or fail-closed fallback. Editable `DRAFT` Registry state cannot be used to construct a trusted index.

### R7.4 — Projection contracts

`IMPLEMENTED_STABLE`

Four standard projections are implemented:

- `MINIMAL` — IDs, title, jurisdiction/domain classification for discovery.
- `SUMMARY` — minimal fields plus summary or source classification and freshness context.
- `EVIDENCE` — summary plus source locator/citation identity, required evidence, source status, review state, and interpretation boundary where applicable.
- `FULL` — complete canonical records only when explicitly required.

Projection changes payload shape only. Exact canonical source and obligation identities remain bound in the receipt.

### R7.5 — Query planner and context budget

`IMPLEMENTED_STABLE`

The deterministic planner supports jurisdiction, provider, domain, source ID, obligation ID, field projection, detail level, limit/cursor, freshness inclusion, and maximum context bytes.

The planner projects before representation selection. TOON remains derived and is selected only when its measured byte size is smaller than compact JSON. If the bounded response envelope cannot fit the requested context budget, the query fails closed.

### R7.6 — Shared query gateway

`IMPLEMENTED_STABLE`

One deterministic query core serves direct local calls and the CLI surface and defines the selection semantics that future transports must reuse. This prevents consumer-side query drift.

Backend precedence for the implemented direct surface is:

1. `DIRECT_LOCAL_INDEXED_GATEWAY` when a verified trusted-release index is supplied;
2. `DIRECT_LOCAL_JSON_QUERY` otherwise.

### R7.7 — Read-only MCP adapter

`IMPLEMENTED_READ_ONLY_TRANSPORT`

Future surface:

- `registry_status`
- `registry_query`
- `registry_get`
- `registry_relations`
- `registry_freshness`
- `registry_delta`

The future MCP adapter cannot mutate Registry records, publish releases, infer legal applicability, or expand authority. `cap.transport.mcp.v1` must not be published before this phase is implemented and validated.

### R7.8 — Trusted-release cache integration

`IMPLEMENTED_VALIDATED`

Normal consumers should verify an immutable trusted Registry release, install the canonical JSON bundle, then build the derived read index locally. The index is rebuildable and is not a replacement for the trusted release.

### R7.9 — Efficiency benchmark

`IMPLEMENTED_VALIDATED`

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

The source implementation now satisfies the R7.1-R7.9 subset of this gate, including MCP/direct parity and recorded benchmark evidence. Full program completion still requires governed trusted `registry-v0.4.0` publication and final joint R7/O7 conformance against that immutable release.

## Planned release boundary

The intended feature release is `registry-v0.4.0`, after R7 implementation and joint R7/O7 conformance validation. Release publication remains a separate governed transition. No trusted `registry-v0.4.0` publication is claimed by the stable direct-surface implementation.

## Cross-repository dependency

Orchestra consumes R7 through the optional O7 phase. The stable direct R7.1-R7.6 surface satisfies Orchestra's frozen runtime entry condition for O7.1 through O7.6. R7 preserves the existing `cap.query.v1` contract so current Orchestra O1-O6 remains compatible when R7 optimization capabilities are absent or unused.

See the Orchestra plan: `docs/architecture/REGISTRY_QUERY_OPTIMIZATION_O7.md` in `Baelfyre/Orchestra`.


## R7.7-R7.9 implementation evidence

- R7.7 MCP adapter: `scripts/r7_mcp_server.py`, read-only stdio transport with the frozen six-tool surface and direct-gateway delegation.
- R7.8 trusted-release integration: `scripts/r7_trusted_release.py`, which verifies release/bundle/member digests before installation and only then permits deterministic index construction.
- R7.9 benchmark: `scripts/r7_benchmark.py` and `tests/test_r7_benchmark.py`, covering all seven frozen comparison modes.
- `TOKEN_EFFICIENCY_NOT_CLAIMED_WITHOUT_HOST_MEASUREMENT`: the benchmark records host-reported tokens as unavailable when they are unavailable and may establish only measured byte savings in that case.
- `registry-v0.4.0` remains unpublished until separate joint-conformance and publication gates complete.
