# Orchestra Compliance Registry

Public, versioned compliance intelligence for Orchestra.

## Status

**FOUNDATION / SOURCE-BACKED PILOT / registry-v0.1.0 TRUSTED RELEASE PUBLISHED**

This repository is the canonical public registry for Orchestra compliance intelligence. Canonical `main` remains editable `DRAFT` source state and must not be treated as a trusted distribution merely because it is public or internally valid.

The first trusted distribution, `registry-v0.1.0`, is published as a non-draft, non-prerelease, immutable GitHub Release from canonical commit `3821bcb55125b4d8864f28b6423650e6e17ac67b`. Its release sequence is `1`, release-manifest SHA-256 is `9922ddcce77dfac0c01cac80fe6669aaffe37636826a56a4b54a8312558ee2d1`, and bundle SHA-256 is `b64889933d30a8dea27bcbbb95c952e4f053c14a4f345e1e04b27777b5025ec0`.

These are intentionally separate states:

- canonical Registry `main`: editable `DRAFT` source state, release sequence `0`;
- published distribution: immutable `registry-v0.1.0` trusted release, release sequence `1`.

See `docs/REGISTRY_V0_1_0_RELEASE_READINESS.md` for the revision-bound candidate evidence that preceded publication. The live GitHub Release is the authoritative publication-state boundary.

## Trust boundary

- Public read access does not grant authority to modify canonical registry state.
- Registry records provide sourced compliance intelligence, not legal advice, project-specific applicability decisions, execution authority, deployment authority, release authority, or policy activation.
- Contributions and source-monitor output are untrusted until validated and approved through the governed repository workflow.
- Orchestra users should use verified versioned releases or an explicitly pinned local snapshot, not arbitrary live `main` content.

## Current source-backed pilot

The first bounded data pilot covers Philippine privacy/data-protection sources published by the National Privacy Commission. It establishes the registry mechanics for source identity, source-status parity, review cadence, direct source locators, evidence-oriented obligations, and fail-closed freshness handling before the broader jurisdiction/provider catalog is populated.

Canonical source state deliberately remains `DRAFT`:

- source presence and currentness are verified against primary NPC publications;
- obligation records preserve source IDs and section locators rather than presenting project-specific legal conclusions;
- Governor remains responsible for applicability and material interpretation;
- every source must have matching `source-status.json` and `review-due.json` entries;
- a missed review date fails validation unless the source is explicitly marked `REVIEW_OVERDUE`;
- Registry Validation also runs on a daily schedule so freshness debt cannot remain invisible indefinitely.

See `docs/PH_PRIVACY_PILOT.md` for the bounded source set and interpretation boundary.

## Deterministic release candidates and trusted publication

`scripts/build_release.py` can transform validated `DRAFT` Registry source state into a deterministic **candidate bundle** without modifying the canonical source files. The candidate contains a `TRUSTED_RELEASE` staging manifest, exact SHA-256 inventory, external `release-manifest.sha256`, and `orchestra-compliance-registry.zip.sha256` evidence.

Candidate construction is not publication. Content hashes establish integrity, while trusted provenance requires the separately governed immutable GitHub Release boundary, or an independently obtained release-manifest SHA-256 for offline installation. CI builds and preserves candidates as revision-bound workflow artifacts so packaging remains continuously testable without silently turning branch content into a trusted release.

`registry-v0.1.0` has completed that separate publication transition and is the current trusted release. Future candidates remain untrusted until their own governed publication and independent verification complete.

See `docs/RELEASE_PACKAGING.md` for the bundle contract, deterministic-build rules, and publication gate, and `docs/REGISTRY_V0_1_0_RELEASE_READINESS.md` for the first candidate's readiness evidence.

## Planned registry domains

- Jurisdictions: Philippines, EU/EEA, United States, Canada, Mexico
- Standards: accessibility, privacy, security, software quality
- Providers: Apple, Google, Microsoft/Windows, Linux distribution ecosystems
- Source freshness, supersession, applicability, provenance, and review tracking

## Security

Canonical changes use the active protected pull-request ruleset, required Registry Validation, Squash-only promotion, immutable release manifests, and least-privilege automation. Trusted publication remains a separate release transition.
