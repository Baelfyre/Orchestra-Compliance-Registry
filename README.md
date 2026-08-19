# Orchestra Compliance Registry

Public, versioned compliance intelligence for Orchestra.

## Status

**INTERNATIONAL SOURCE-BACKED PILOT IN EDITABLE DRAFT / registry-v0.1.0 TRUSTED RELEASE PUBLISHED**

This repository is the canonical public registry for Orchestra compliance intelligence. Canonical `main` remains editable `DRAFT` source state and must not be treated as a trusted distribution merely because it is public or internally valid.

The current trusted distribution, `registry-v0.1.0`, remains the immutable Philippine privacy pilot published from canonical commit `3821bcb55125b4d8864f28b6423650e6e17ac67b`. The editable source on `main` is advancing separately as `0.2.0-dev.1` to establish a bounded international privacy pilot.

These states are intentionally separate:

- canonical Registry `main`: editable `DRAFT` source state, currently `0.2.0-dev.1`, release sequence `0`;
- published distribution: immutable `registry-v0.1.0` trusted release, release sequence `1`.

## Current jurisdiction coverage

Coverage status describes Registry data maturity, not legal applicability or completeness.

| Jurisdiction | Registry status | Current source-backed scope |
| --- | --- | --- |
| Philippines | `SOURCE_BACKED_PILOT` | Data Privacy Act, implementing rules, selected NPC security and privacy-engineering issuances |
| EU / EEA | `SOURCE_BACKED_PILOT` | GDPR primary regulation with selected design, security, and DPIA obligations |
| Canada | `SOURCE_BACKED_PILOT` | Federal PIPEDA with selected accountability and safeguard obligations; pending changes are tracked explicitly |
| Australia | `SOURCE_BACKED_PILOT` | Privacy Act 1988 with selected Australian Privacy Principle obligations |
| Singapore | `SOURCE_BACKED_PILOT` | Personal Data Protection Act 2012 with selected protection and retention obligations |
| United States | `FOUNDATION_ONLY` | Jurisdiction model exists, but no federal/state obligation set is asserted yet |
| Mexico | `FOUNDATION_ONLY` | Jurisdiction model exists, but no source-backed obligation set is asserted yet |

`SOURCE_BACKED_PILOT` means the Registry contains verified primary sources and a bounded set of evidence-oriented obligations. It does not mean exhaustive coverage of the jurisdiction, all sectoral laws, all subjurisdictions, all regulatory guidance, or project-specific legal applicability.

See `docs/INTERNATIONAL_PRIVACY_PILOT.md` for the international scope and `docs/PH_PRIVACY_PILOT.md` for the original Philippine pilot.

## Machine-first representation

Registry machine state is JSON-first. Markdown is a human-readable reference and must not be parsed to reconstruct machine state when a corresponding JSON record exists.

Machine entry points:

- `registry/manifest.json`: editable Registry source-state authority and canonical record map;
- `machine/publication-state.json`: machine-readable publication index for current source and trusted release identity;
- `machine/representation-policy.json`: representation rules separating machine authority, external publication reality, and human-readable views;
- `registry/*.json`: compliance data, source status, review state, and other Registry records referenced by the manifest.

The immutable GitHub Release remains external publication reality and must be re-read before trust or mutation. `machine/publication-state.json` records the last verified publication identity so agents and tooling do not need to reconstruct it from Markdown.

Human-facing files such as this README, `GOVERNANCE.md`, and files under `docs/` explain the machine records. They do not override them.

## Trust boundary

- Public read access does not grant authority to modify canonical registry state.
- Registry records provide sourced compliance intelligence, not legal advice, project-specific applicability decisions, execution authority, deployment authority, release authority, or policy activation.
- A jurisdiction being `SOURCE_BACKED_PILOT` does not establish that a listed obligation applies to a particular project, organization, person, product, or processing activity.
- Contributions and source-monitor output are untrusted until validated and approved through the governed repository workflow.
- Orchestra users should use verified versioned releases or an explicitly pinned local snapshot, not arbitrary live `main` content.

## Source-backed pilot rules

The international pilot preserves the original fail-closed mechanics:

- sources must resolve to primary authority publications;
- obligation records preserve source IDs and direct locators rather than presenting project-specific legal conclusions;
- Governor remains responsible for applicability and material interpretation;
- every source must have matching `source-status.json` and `review-due.json` entries;
- a missed review date fails validation unless the source is explicitly marked `REVIEW_OVERDUE`;
- jurisdictions without a reviewed source and obligation set remain `FOUNDATION_ONLY`;
- broader national, state, provincial, territorial, sectoral, and regulatory coverage must be added explicitly rather than inferred.

Registry Validation also runs on a daily schedule so freshness debt cannot remain invisible indefinitely.

## Deterministic release candidates and trusted publication

`scripts/build_release.py` can transform validated `DRAFT` Registry source state into a deterministic candidate bundle without modifying the canonical source files. The candidate contains a `TRUSTED_RELEASE` staging manifest, exact SHA-256 inventory, external `release-manifest.sha256`, and `orchestra-compliance-registry.zip.sha256` evidence.

Candidate construction is not publication. Content hashes establish integrity, while trusted provenance requires the separately governed immutable GitHub Release boundary, or an independently obtained release-manifest SHA-256 for offline installation. CI builds and preserves candidates as revision-bound workflow artifacts so packaging remains continuously testable without silently turning branch content into a trusted release.

Machine metadata under `machine/` is intentionally outside the distributed `registry/` root. It must not silently change the trusted Registry bundle inventory or the immutable v0.1.0 release identity.

`registry-v0.1.0` remains the current trusted release. The international `0.2.0-dev.1` source state is not a trusted release until its own governed publication and independent verification complete.

See `docs/RELEASE_PACKAGING.md` for the bundle contract and publication gate.

## Planned expansion

The Registry can expand by independently reviewed jurisdiction and domain slices rather than claiming generic worldwide compliance.

Current priority areas include:

- additional privacy and data-protection jurisdictions;
- US federal and state/subjurisdiction modeling;
- Canadian provincial overlap and substantially similar laws;
- Australian state/territory and sectoral overlap;
- accessibility requirements;
- security and software-quality standards;
- provider and distribution requirements;
- source freshness, supersession, applicability, provenance, and review tracking.

## Contributing

Contributions are welcome when they preserve the Registry trust model. New legal or regulatory records should identify a primary authority source, jurisdiction, direct source locator, evidence-oriented obligation, source-status entry, and review schedule. Secondary summaries may assist research but should not replace primary authority verification for canonical records.

See `CONTRIBUTING.md` and `GOVERNANCE.md` before proposing registry changes.

## Security

Canonical changes use the active protected pull-request ruleset, required Registry Validation, squash-only promotion, immutable release manifests, and least-privilege automation. Trusted publication remains a separate release transition.
