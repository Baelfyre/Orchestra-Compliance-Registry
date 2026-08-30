# R7 — Token-Efficient Registry Read Architecture

## Status

`IMPLEMENTED_R7_1_R7_9_TRUSTED_V0_4_0_PUBLISHED_O7_7_CONFORMANCE_COMPLETE`

R7.1 through R7.9 are implemented and validated. Canonical `registry/*.json` records remain the source of truth. The implementation provides deterministic typed entities, derived relationships, a disposable trusted-release SQLite index, bounded projections, context-budget enforcement, a shared direct query gateway, read-only MCP transport, trusted-release verification/cache installation, and evidence-based efficiency benchmarking.

`IMPLEMENTED_READ_ONLY_TRANSPORT`

Trusted `registry-v0.4.0` is published as a non-draft, non-prerelease, immutable release, and canonical Orchestra records O7.7 as `CANONICAL_MERGED_VERIFIED` with latest joint-conformance evidence `PASS`. Registry R7 is therefore terminal for the R7/O7 boundary. This state does not authorize Registry mutation, release publication, Orchestra execution, automatic merge, legal interpretation, or project applicability decisions.

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

The frozen Orchestra O7 entry token `IMPLEMENTED_STABLE_REGISTRY_R7_SURFACE_REQUIRED` was originally scoped to O7.1 through O7.6 runtime implementation. O7.7 remained a separate governed joint-conformance transition. That separate transition has since completed and is recorded in canonical Orchestra; the original token semantics are preserved rather than retroactively expanded.

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

One deterministic query core serves direct local calls and the CLI surface and defines the selection semantics that all transports reuse. This prevents consumer-side query drift.

Backend precedence for the implemented direct surface is:

1. `DIRECT_LOCAL_INDEXED_GATEWAY` when a verified trusted-release index is supplied;
2. `DIRECT_LOCAL_JSON_QUERY` otherwise.

### R7.7 — Read-only MCP adapter

`IMPLEMENTED_READ_ONLY_TRANSPORT`

Implemented surface:

- `registry_status`
- `registry_query`
- `registry_get`
- `registry_relations`
- `registry_freshness`
- `registry_delta`

The MCP adapter cannot mutate Registry records, publish releases, infer legal applicability, or expand authority. `cap.transport.mcp.v1` is descriptive and optional.

### R7.8 — Trusted-release cache integration

`IMPLEMENTED_VALIDATED`

Normal consumers verify an immutable trusted Registry release, install the canonical JSON bundle, then build the derived read index locally. The index is rebuildable and is not a replacement for the trusted release.

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

`TOKEN_EFFICIENCY_NOT_CLAIMED_WITHOUT_HOST_MEASUREMENT`

Token-efficiency benefit must remain evidence-derived; it must not be claimed from design intent alone. Host-reported input-token measurements were unavailable in the recorded benchmark boundary, so token-efficiency benefit is not established by R7 completion itself.

## Completion gate

R7 requires:

- canonical JSON authority unchanged;
- all existing Registry validations green;
- v0.3 compatibility preserved;
- deterministic index rebuild;
- index-to-JSON semantic parity;
- projection parity;
- query receipt parity;
- MCP-to-direct-query parity;
- authority expansion false;
- efficiency evidence recorded;
- trusted `registry-v0.4.0` publication verified;
- final joint R7/O7 conformance completed against that immutable release.

The source implementation satisfies the R7.1-R7.9 gate. Trusted `registry-v0.4.0` is published and immutable-verified, and canonical Orchestra records final O7.7 joint conformance as complete. R7 is therefore complete for this governed program boundary. This completion does not establish token-efficiency benefit where host token measurements are unavailable and does not expand authority.

## Published release boundary

The R7 feature release is `registry-v0.4.0`.

Publication identity:

- release sequence: `4`;
- source commit: `488c979b37dd84d8645fd8e6c288d297375c4e5b`;
- source tree: `0d3bbf34ec7ab7e4833fba225aba96b829de1cec`;
- release manifest SHA-256: `040d6576cf10e9f7e3a9a051792869541c1d33b7af3c665fad8eecb939c7baaa`;
- bundle SHA-256: `e0457a75837d169d7bb8a7da14d8f4141d35a691952ff8f8978ef793e3cf92d3`;
- state: `PUBLISHED_IMMUTABLE_VERIFIED`.

Publication remains a separate governed transition from ordinary canonical source merges. The completed release does not grant future publication authority.

## Cross-repository dependency

Orchestra consumes R7 through the optional O7 phase. R7 preserves the existing `cap.query.v1` contract so current Orchestra O1-O6 compatibility remains available when R7 optimization capabilities are absent or unused.

Canonical Orchestra now records:

- trusted `registry-v0.4.0` as the Registry dependency;
- R7 direct JSON, indexed, and optional MCP transports as available;
- O7.1 through O7.7 as `CANONICAL_MERGED_VERIFIED`;
- latest joint-conformance evidence as `PASS`;
- `joint_r7_o7_conformance_complete = true`;
- no authority expansion and no release-integration authority from that state.

See the Orchestra plan and runtime-state contract under `docs/architecture/REGISTRY_QUERY_OPTIMIZATION_O7.md` and `docs/architecture/contracts/registry-o7-runtime-state.v1.json` in `Baelfyre/Orchestra`.

## R7.7-R7.9 and terminal evidence

- R7.7 MCP adapter: `scripts/r7_mcp_server.py`, read-only stdio transport with the frozen six-tool surface and direct-gateway delegation.
- R7.8 trusted-release integration: `scripts/r7_trusted_release.py`, which verifies release/bundle/member digests before installation and only then permits deterministic index construction.
- R7.9 benchmark: `scripts/r7_benchmark.py` and `tests/test_r7_benchmark.py`, covering all seven frozen comparison modes.
- `TOKEN_EFFICIENCY_NOT_CLAIMED_WITHOUT_HOST_MEASUREMENT`: the benchmark records host-reported tokens as unavailable when they are unavailable and may establish only measured evidence that is actually observed.
- Trusted `registry-v0.4.0` is published and immutable-verified; machine release evidence is `machine/release-evidence-v0.4.0.json`.
- Final Orchestra O7.7 joint conformance is complete and canonical.
