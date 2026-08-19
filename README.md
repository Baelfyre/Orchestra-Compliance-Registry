# Orchestra Compliance Registry

**Public, versioned compliance intelligence for governed software and AI-assisted development.**

The Registry turns reviewed compliance sources into structured, evidence-oriented records that humans and AI tooling can query without treating documentation, validation, or source discovery as legal advice or execution authority.

> **Machine entry point:** [`README.json`](README.json)  
> **Editable source state:** `0.2.0-dev.1` / `DRAFT`  
> **Current trusted release:** `registry-v0.1.0`

## Purpose

The Registry is designed to help software projects identify compliance considerations across jurisdictions, technical domains, and platform/provider requirements while preserving source provenance, freshness, applicability review, and explicit trust boundaries.

Current source-backed work is an **international privacy pilot**. Broader software-development, cybersecurity, database/data-governance, AI, and provider/platform coverage is the next expansion program.

## How to use it

| Audience | Start here | Use for |
| --- | --- | --- |
| Humans | `README.md` | Quick orientation, coverage, usage, and trust boundaries |
| AI / agents / tooling | [`README.json`](README.json) | Complete repository map and ordered machine-readable references |
| Registry consumers | [`registry/manifest.json`](registry/manifest.json) | Canonical editable record map and source-state identity |
| Release consumers | [`machine/publication-state.json`](machine/publication-state.json) | Last verified publication identity; live release must still be reverified |
| Contributors | [`CONTRIBUTING.md`](CONTRIBUTING.md) | Source, evidence, review, and contribution requirements |

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
| `machine/*.json` | Publication, representation, and control metadata | Machine control/reference state as defined per record |
| JSON Schema | Deterministic machine-contract validation | Validation contract |
| TOON | Optional compact AI context projection | Derived, non-authoritative |

When prose and a machine record disagree on an exact deterministic fact, use the machine record and treat the mismatch as documentation drift.

## Trust boundary

- Registry records provide sourced compliance intelligence, **not legal advice**.
- Applicability to a specific product, organization, user, sector, or processing activity requires explicit review.
- A platform rule can be mandatory for distribution without being a law.
- A government or industry framework can be highly relevant without itself being legally binding.
- Validation proves internal consistency; it does not create legal applicability or publication authority.
- Trusted distribution requires the separately governed immutable release boundary.

## Go deeper

| Topic | Human reference | Machine reference |
| --- | --- | --- |
| Repository overview | `README.md` | [`README.json`](README.json) |
| Governance | [`GOVERNANCE.md`](GOVERNANCE.md) | [`machine/representation-policy.json`](machine/representation-policy.json) |
| Registry records | Documentation and pilot notes | [`registry/manifest.json`](registry/manifest.json) |
| Publication state | [`docs/RELEASE_PACKAGING.md`](docs/RELEASE_PACKAGING.md) | [`machine/publication-state.json`](machine/publication-state.json) |
| International privacy pilot | [`docs/INTERNATIONAL_PRIVACY_PILOT.md`](docs/INTERNATIONAL_PRIVACY_PILOT.md) | `registry/jurisdictions.json`, `registry/sources.json`, `registry/obligations.json` |
| Contributions | [`CONTRIBUTING.md`](CONTRIBUTING.md) | JSON Schemas under `schema/` |

Canonical changes remain pull-request governed. A trusted Registry release is a separate publication transition.
