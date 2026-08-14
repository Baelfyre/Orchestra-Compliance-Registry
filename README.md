# Orchestra Compliance Registry

Public, versioned compliance intelligence for Orchestra.

## Status

**FOUNDATION / SOURCE-BACKED PILOT / v0.1.0 CANDIDATE READY / NOT YET A TRUSTED COMPLIANCE RELEASE**

This repository is the canonical public registry for Orchestra compliance intelligence. Until a versioned registry release has passed the repository validation and approval process, users must treat its contents as draft data rather than an authoritative compliance determination.

The deterministic `registry-v0.1.0` candidate is prepared and reproducible from canonical source state, but publication remains a separate protected transition. See `docs/REGISTRY_V0_1_0_RELEASE_READINESS.md` for the exact source baseline, hashes, freshness state, and publication prerequisites.

## Trust boundary

- Public read access does not grant authority to modify canonical registry state.
- Registry records provide sourced compliance intelligence, not legal advice, project-specific applicability decisions, execution authority, deployment authority, release authority, or policy activation.
- Contributions and source-monitor output are untrusted until validated and approved through the governed repository workflow.
- Orchestra users should use verified versioned releases or an explicitly pinned local snapshot, not arbitrary live `main` content.

## Current source-backed pilot

The first bounded data pilot covers Philippine privacy/data-protection sources published by the National Privacy Commission. It establishes the registry mechanics for source identity, source-status parity, review cadence, direct source locators, evidence-oriented obligations, and fail-closed freshness handling before the broader jurisdiction/provider catalog is populated.

The pilot deliberately remains `DRAFT`:

- source presence and currentness are verified against primary NPC publications;
- obligation records preserve source IDs and section locators rather than presenting project-specific legal conclusions;
- Governor remains responsible for applicability and material interpretation;
- every source must have matching `source-status.json` and `review-due.json` entries;
- a missed review date fails validation unless the source is explicitly marked `REVIEW_OVERDUE`;
- Registry Validation also runs on a daily schedule so freshness debt cannot remain invisible indefinitely.

See `docs/PH_PRIVACY_PILOT.md` for the bounded source set and interpretation boundary.

## Deterministic release candidates

`scripts/build_release.py` can transform validated `DRAFT` Registry source state into a deterministic **candidate bundle** without modifying the canonical source files. The candidate contains a `TRUSTED_RELEASE` staging manifest, exact SHA-256 inventory, external `release-manifest.sha256`, and `orchestra-compliance-registry.zip.sha256` evidence.

Candidate construction is not publication. Content hashes establish integrity, while trusted provenance still requires the separately governed immutable GitHub Release boundary—or an independently obtained release-manifest SHA-256 for offline installation. CI builds and preserves the candidate as a revision-bound workflow artifact so packaging remains continuously testable without silently turning branch content into a trusted release.

See `docs/RELEASE_PACKAGING.md` for the bundle contract, deterministic-build rules, and publication gate, and `docs/REGISTRY_V0_1_0_RELEASE_READINESS.md` for the first candidate's readiness evidence.

## Planned registry domains

- Jurisdictions: Philippines, EU/EEA, United States, Canada, Mexico
- Standards: accessibility, privacy, security, software quality
- Providers: Apple, Google, Microsoft/Windows, Linux distribution ecosystems
- Source freshness, supersession, applicability, provenance, and review tracking

## Security

Canonical changes use the active protected pull-request ruleset, required Registry Validation, Squash-only promotion, immutable release manifests, and least-privilege automation. Trusted publication remains a separate release transition.
