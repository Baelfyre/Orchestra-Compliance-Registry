# Orchestra Compliance Registry

**Public, versioned compliance intelligence for governed software and AI-assisted development.**

The Registry turns reviewed compliance sources into structured, evidence-oriented records that humans and AI tooling can query without treating documentation, validation, or source discovery as legal advice or execution authority.

> **Machine entry point:** [`README.json`](README.json)  
> **Editable source state:** `0.2.0-dev.1` / `DRAFT`  
> **Current trusted release:** `registry-v0.4.0`

## Purpose

The Registry is designed to help software projects identify compliance considerations across jurisdictions, technical domains, and platform/provider requirements while preserving source provenance, freshness, applicability review, and explicit trust boundaries.

The current trusted distribution combines the bounded **international privacy pilot**, canonical official-source monitoring, capability negotiation and release-delta contracts, and the completed R7 token-efficient read surface. Broader software-development, cybersecurity, database/data-governance, AI, accessibility, and provider/platform source-backed coverage remains the next expansion program.

## How to use it

| Audience | Start here | Use for |
| --- | --- | --- |
| Humans | `README.md` | Quick orientation, coverage, usage, and trust boundaries |
| AI / agents / tooling | [`README.json`](README.json) | Complete repository map and ordered machine-readable references |
| Registry consumers | [`registry/manifest.json`](registry/manifest.json) | Canonical editable record map and source-state identity |
| Adaptive consumers | [`docs/ADAPTIVE_CONSUMPTION_CONTRACTS.md`](docs/ADAPTIVE_CONSUMPTION_CONTRACTS.md) | R5 capability negotiation and R6 release-delta compatibility contracts |
| R7 consumers | [`docs/TOKEN_EFFICIENT_QUERY_ARCHITECTURE_R7.md`](docs/TOKEN_EFFICIENT_QUERY_ARCHITECTURE_R7.md) | Deterministic query, projection, trusted-cache, MCP, and benchmark architecture |
| Source reviewers | [`docs/SOURCE_PROVENANCE_AUDIT.md`](docs/SOURCE_PROVENANCE_AUDIT.md) | Official citations, date provenance, and the latest source rerun |
| Source-monitor reviewers | [`docs/SOURCE_MONITORING.md`](docs/SOURCE_MONITORING.md) | Dynamic official-source monitoring, fingerprints, change states, and automation boundaries |
| Release consumers | [`docs/REGISTRY_V0_4_0_RELEASE_EVIDENCE.md`](docs/REGISTRY_V0_4_0_RELEASE_EVIDENCE.md) | Human-readable trusted-release identity, integrity, and terminal R7/O7 evidence |
| Release tooling / agents | [`machine/release-evidence-v0.4.0.json`](machine/release-evidence-v0.4.0.json) | Machine-readable exact release ID, source identity, hashes, assets, and workflow evidence |
| Contributors | [`CONTRIBUTING.md`](CONTRIBUTING.md) | Source, evidence, review, and contribution requirements |

## Trusted release

`registry-v0.4.0` was published on **2026-08-28** as a non-draft, non-prerelease, immutable GitHub Release from exact source commit `488c979b37dd84d8645fd8e6c288d297375c4e5b` and source tree `0d3bbf34ec7ab7e4833fba225aba96b829de1cec`.

| Evidence | SHA-256 |
| --- | --- |
| Release manifest | `040d6576cf10e9f7e3a9a051792869541c1d33b7af3c665fad8eecb939c7baaa` |
| Registry bundle | `e0457a75837d169d7bb8a7da14d8f4141d35a691952ff8f8978ef793e3cf92d3` |

Release ID: `378292109`  
Publication workflow run: `33147297345`  
Machine evidence: [`machine/release-evidence-v0.4.0.json`](machine/release-evidence-v0.4.0.json)

The editable repository remains `0.2.0-dev.1` `DRAFT` source state. Trusted publication is staged by the deterministic release builder and does not rewrite editable source records.

## Source provenance

Canonical sources are **official primary sources only**. Government and regulatory records must use the issuing government, regulator, or official legislation service. Provider/platform records must use the provider's own official developer, policy, legal, security, compliance, or documentation site. Wikipedia, social media, blogs, aggregators, and secondary summaries cannot replace an available official primary source.

Every source records an official citation and source locator plus the dates supported by the authority, including issuance/publication, entry into force, application, current text/version, last amendment, gathering, and verification where available. Dates are left unset rather than guessed when the reviewed official source does not establish an exact value.

**Latest provenance rerun:** `2026-08-19`  
Human audit: [`docs/SOURCE_PROVENANCE_AUDIT.md`](docs/SOURCE_PROVENANCE_AUDIT.md)  
Machine audit: [`machine/source-provenance-audit.v1.json`](machine/source-provenance-audit.v1.json)

## Dynamic source monitoring

The canonical source-monitor subsystem tracks all eight current canonical official sources against a reviewed fingerprint baseline. It is configured for six-hour polling through `.github/workflows/source-monitor.yml` using `HTML_NORMALIZED_TEXT` or `BINARY_SHA256` according to the official source surface.

| Behavior | Automation |
| --- | --- |
| Fetch official canonical sources and verify authority-domain redirects | Automatic |
| Compare live fingerprints with the reviewed baseline | Automatic |
| Preserve machine-readable source-watch evidence | Automatic |
| Open a bounded **draft** candidate PR for a potential substantive change or source move | Automatic |
| Determine project/legal applicability | Human/Governor review required |
| Extract or rewrite legal obligations from detected page changes | Not automatic |
| Accept a new reviewed source baseline | Not automatic |
| Merge a source-change candidate | Not automatic |
| Publish a trusted Registry release | Not automatic |

The current reviewed monitor baseline is `ACTIVE`, covers all eight canonical sources, and was captured from the official primary-source endpoints on `2026-08-19T15:36:28Z`. A detected substantive fingerprint change is evidence that the source must be reviewed; it is **not** itself proof that a law, regulation, obligation, or project applicability changed.

See [`docs/SOURCE_MONITORING.md`](docs/SOURCE_MONITORING.md) for the monitoring architecture. Machine controls are [`machine/source-monitor-policy.json`](machine/source-monitor-policy.json) and [`machine/source-monitor-baseline.v1.json`](machine/source-monitor-baseline.v1.json).

The source-monitor implementation is canonical on `main`, first entered trusted distribution in `registry-v0.3.0`, and remains included in immutable `registry-v0.4.0`. Monitoring remains evidence-only and cannot automatically publish a future trusted release.

## Adaptive consumption contracts

Registry R5-R6 are canonical on `main` and provide a machine-readable compatibility surface for adaptive consumers:

- `registry/capabilities.json` declares descriptive, versioned capabilities without granting legal, applicability, execution, merge, or release authority.
- `schema/capability-manifest.schema.json` validates the closed R5 capability contract.
- `schema/release-delta.schema.json` validates R6 release-delta evidence.
- `scripts/release_delta.py` deterministically compares Registry roots and classifies compatible, revalidation, unsupported-capability, and human-review impacts.

The canonical R5 capability manifest was reconciled byte-for-byte with Orchestra's O1-O6 compatibility fixture before Registry R1-R6 merged. `registry-v0.3.0` was the first trusted release containing R5-R6; `registry-v0.4.0` preserves those contracts and adds the trusted R7 surface. Consumers pinned to immutable `registry-v0.2.0` must continue using Orchestra's explicit v0.2 legacy compatibility profile rather than inventing capability metadata that release did not contain.

See [`docs/ADAPTIVE_CONSUMPTION_CONTRACTS.md`](docs/ADAPTIVE_CONSUMPTION_CONTRACTS.md).

## Token-efficient query architecture

**R7.1 through R7.9 are implemented and validated; trusted `registry-v0.4.0` is published and immutable-verified; canonical Orchestra O7.7 joint conformance is complete and `PASS`.** Canonical Registry JSON remains authority. R7 adds deterministic typed reads, a rebuildable verified-release index, bounded projections/context budgets, trusted-release verification/cache installation, and a read-only MCP transport that delegates to the same query gateway.

Machine terminal state: [`machine/r7-surface.v1.json`](machine/r7-surface.v1.json)  
Human architecture: [`docs/TOKEN_EFFICIENT_QUERY_ARCHITECTURE_R7.md`](docs/TOKEN_EFFICIENT_QUERY_ARCHITECTURE_R7.md)

R7 completion does **not** establish token-efficiency benefit where host-reported input-token measurement is unavailable. It also does not expand Registry, legal, merge, release, execution, or project-applicability authority.

## Jurisdiction coverage

`SOURCE_BACKED_PILOT` means reviewed primary sources and a bounded obligation set exist. It does **not** mean exhaustive legal coverage or automatic project applicability.

| Jurisdiction | Status | Current scope |
| --- | --- | --- |
| Philippines | `SOURCE_BACKED_PILOT` | Privacy, data protection, security, privacy engineering |
| EU / EEA | `SOURCE_BACKED_PILOT` | GDPR design/default, security, DPIA |
| Canada | `SOURCE_BACKED_PILOT` | Federal PIPEDA accountability and safeguards |
| Australia | `SOURCE_BACKED_PILOT` | Privacy Act / APP governance, security, retention |
| Singapore | `SOURCE_BACKED_PILOT` | PDPA protection and retention |
| United States | `FOUNDATION_ONLY` | Federal/state model pending |
| Mexico | `FOUNDATION_ONLY` | Source-backed obligation set pending |

See [`docs/INTERNATIONAL_PRIVACY_PILOT.md`](docs/INTERNATIONAL_PRIVACY_PILOT.md) for the bounded international scope.

## Compliance topics

| Topic | Current state | Examples |
| --- | --- | --- |
| Privacy & data protection | `SOURCE_BACKED_PILOT` | Processing, accountability, impact assessment |
| Security | `SOURCE_BACKED_PILOT` | Access control, safeguards, resilience, testing |
| Data lifecycle | `SOURCE_BACKED_PILOT` | Retention, disposal, de-identification |
| Privacy engineering | `SOURCE_BACKED_PILOT` | Privacy by design/default, lifecycle traceability |
| Governance & risk | `SOURCE_BACKED_PILOT` | PIA/DPIA, accountability, management programs |
| Software development | `NEXT_EXPANSION` | Secure development, software assurance, accessibility |
| Database & data governance | `NEXT_EXPANSION` | Data handling, storage, retention, access, residency |
| AI usage & AI systems | `NEXT_EXPANSION` | AI regulation, risk frameworks, model/provider rules |
| Provider/platform requirements | `NEXT_EXPANSION` | App stores, operating systems, cloud and developer platforms |

## Provider and platform catalog

Provider entries currently establish structure only. They are not yet source-backed policy obligation sets.

| Provider / ecosystem | Status |
| --- | --- |
| Apple | `FOUNDATION_ONLY` |
| Google Play | `FOUNDATION_ONLY` |
| Microsoft / Windows | `FOUNDATION_ONLY` |
| Debian | `FOUNDATION_ONLY` |
| Fedora | `FOUNDATION_ONLY` |
| Snap Store | `FOUNDATION_ONLY` |
| Flathub | `FOUNDATION_ONLY` |

The next provider phase will distinguish **contractual platform rules** from **government law/regulation** and from **voluntary technical frameworks**.

## Representation model

| Format | Role | Authority |
| --- | --- | --- |
| `README.md` / `docs/*.md` | Compact human explanation and review material | Non-authoritative human reference |
| `README.json` | Complete machine-readable repository index | Derived and parity-validated index |
| `registry/*.json` | Canonical structured registry records | Editable machine authority as mapped by the manifest |
| `machine/*.json` | Publication, release-evidence, representation, provenance-audit, monitoring, R7, and control metadata | Machine control/reference or evidence state as defined per record |
| JSON Schema | Deterministic machine-contract validation | Validation contract |
| TOON | Optional compact AI context projection | Derived, non-authoritative |

When prose and a machine record disagree on an exact deterministic fact, use the machine record and treat the mismatch as documentation drift.

## Trust boundary

- Registry records provide sourced compliance intelligence, **not legal advice**.
- Applicability to a specific product, organization, user, sector, or processing activity requires explicit review.
- Automated source-change detection is evidence for review, not legal interpretation.
- Capability, release-delta, R7 query, and conformance records are compatibility/evidence surfaces, not execution or publication authority.
- A platform rule can be mandatory for distribution without being a law.
- A government or industry framework can be highly relevant without itself being legally binding.
- Validation proves internal consistency; it does not create legal applicability or publication authority.
- Trusted distribution requires the separately governed immutable release boundary.

## Go deeper

| Topic | Human reference | Machine reference |
| --- | --- | --- |
| Repository overview | `README.md` | [`README.json`](README.json) |
| Trusted v0.4.0 release | [`docs/REGISTRY_V0_4_0_RELEASE_EVIDENCE.md`](docs/REGISTRY_V0_4_0_RELEASE_EVIDENCE.md) | [`machine/release-evidence-v0.4.0.json`](machine/release-evidence-v0.4.0.json) |
| Trusted release history | [`docs/TRUSTED_RELEASE_HISTORY.md`](docs/TRUSTED_RELEASE_HISTORY.md) | [`machine/trusted-release-history.json`](machine/trusted-release-history.json) |
| Source provenance | [`docs/SOURCE_PROVENANCE_AUDIT.md`](docs/SOURCE_PROVENANCE_AUDIT.md) | [`machine/source-provenance-audit.v1.json`](machine/source-provenance-audit.v1.json) |
| Dynamic source monitoring | [`docs/SOURCE_MONITORING.md`](docs/SOURCE_MONITORING.md) | [`machine/source-monitor-policy.json`](machine/source-monitor-policy.json), [`machine/source-monitor-baseline.v1.json`](machine/source-monitor-baseline.v1.json) |
| Adaptive consumption R5-R6 | [`docs/ADAPTIVE_CONSUMPTION_CONTRACTS.md`](docs/ADAPTIVE_CONSUMPTION_CONTRACTS.md) | [`registry/capabilities.json`](registry/capabilities.json), [`schema/release-delta.schema.json`](schema/release-delta.schema.json) |
| R7 query, trusted-cache, MCP, benchmark, and O7.7 boundary | [`docs/TOKEN_EFFICIENT_QUERY_ARCHITECTURE_R7.md`](docs/TOKEN_EFFICIENT_QUERY_ARCHITECTURE_R7.md) | [`machine/r7-surface.v1.json`](machine/r7-surface.v1.json) |
| Governance | [`GOVERNANCE.md`](GOVERNANCE.md) | [`machine/representation-policy.json`](machine/representation-policy.json) |
| Registry records | Documentation and pilot notes | [`registry/manifest.json`](registry/manifest.json) |
| Publication state | [`docs/RELEASE_PACKAGING.md`](docs/RELEASE_PACKAGING.md) | [`machine/publication-state.json`](machine/publication-state.json) |
| International privacy pilot | [`docs/INTERNATIONAL_PRIVACY_PILOT.md`](docs/INTERNATIONAL_PRIVACY_PILOT.md) | `registry/jurisdictions.json`, `registry/sources.json`, `registry/obligations.json` |
| Contributions | [`CONTRIBUTING.md`](CONTRIBUTING.md) | JSON Schemas under `schema/` |

Canonical changes remain pull-request governed. Any future trusted Registry release remains a separate publication transition and requires fresh authorization and verification.
