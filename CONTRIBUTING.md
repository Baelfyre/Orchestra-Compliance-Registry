# Contributing to Orchestra Compliance Registry

Thank you for helping expand the Registry.

This repository accepts source-backed proposals for jurisdictions, obligations, providers, standards, source-status updates, and supporting validation. Contributions must preserve the Registry's provenance, applicability, freshness, and publication boundaries.

## Before contributing

Read:

- `README.md` for current coverage and trust boundaries;
- `GOVERNANCE.md` for the canonical change path and authority model;
- `docs/SOURCE_PROVENANCE_AUDIT.md` for the official-source and date-provenance model;
- `docs/INTERNATIONAL_PRIVACY_PILOT.md` for the current jurisdiction expansion model;
- `registry/manifest.json` for the machine record map.

## Preferred contribution unit

Keep a pull request bounded to one reviewable jurisdiction, source family, provider, or maintenance objective whenever practical.

A new source-backed jurisdiction slice should normally include:

1. An official primary authority record in `registry/sources.json`.
2. One or more evidence-oriented obligations in `registry/obligations.json` only when supported by the reviewed text.
3. A matching entry in `registry/source-status.json`.
4. A matching review schedule in `registry/review-due.json`.
5. The jurisdiction coverage state in `registry/jurisdictions.json`.
6. Updated `registry/manifest.json` counts.
7. Tests or validation changes needed to preserve the fail-closed contract.
8. Human documentation describing scope and known exclusions when the slice materially expands coverage.

## Canonical source requirements

Canonical Registry evidence uses **official primary sources** when the issuing authority or provider publishes the material directly.

- Government, legislation, and regulator material must come from the issuing government, regulator, official legislation service, or equivalent official authority site.
- Provider and platform requirements must come from that provider's official developer, policy, legal, security, compliance, trust, or product-documentation site.
- Standards and technical frameworks must come from the publishing standards body or official framework owner.
- Wikipedia, social media, blogs, community posts, aggregators, search-result summaries, AI-generated explanations, and secondary legal explainers must not be used as canonical evidence when an official primary source is available.
- Secondary material may assist discovery, but it must not replace the official source citation in a canonical record.

A source contribution must identify:

- stable source ID;
- official title;
- source type;
- issuing authority or publisher;
- canonical HTTPS source URL;
- structured official citation and source identifier;
- direct section, article, schedule, page, policy clause, or equivalent locator;
- jurisdiction IDs and relevant domains;
- source gathering and verification dates;
- supported legal/version dates;
- current verification status;
- explicit interpretation boundary.

The canonical URL and structured citation must point to the same official source. The recorded authority domain must match the official source host.

## Date provenance

Capture only dates supported by the official source:

- `issued_date`: assent, promulgation, adoption, signature, or issuance;
- `publication_date`: official publication where distinct;
- `effective_date`: entry into force or commencement;
- `applicable_date`: date relevant provisions became applicable where distinct;
- `current_text_as_of`: date/version of the consolidated text reviewed;
- `last_amended_date`: latest amendment date stated by the authority;
- `gathered_at`: date the Registry retrieved the source;
- `verification.verified_at`: date the Registry checked source identity/currentness.

Do not infer an exact date merely to complete a field. If the reviewed official source does not establish an exact date, leave the field unset and explain the limitation in `date_reference_note`.

## Provider and platform rules

Provider/platform requirements are a separate authority class from law and regulation.

A provider record must identify the exact provider surface and official company source. A rule may be contractually mandatory for app distribution, cloud or service use, API access, certification, or platform participation while still **not being legislation**.

Do not label provider policy as statute or regulation. Do not label voluntary technical guidance as binding law.

## Obligation writing rules

Obligations should be evidence-oriented and source-bound.

Do:

- summarize the reviewed legal, regulatory, or provider text narrowly;
- preserve a direct source locator;
- identify evidence that a software or governance workflow could inspect;
- require Governor applicability review.

Do not:

- state that a law automatically applies to a project or organization;
- present the Registry as legal advice or legal certification;
- infer missing requirements from general best practice;
- combine materially different jurisdictions into a generic obligation when their scope differs;
- turn secondary commentary into canonical legal authority.

## Coverage states

Use `SOURCE_BACKED_PILOT` only when the jurisdiction has reviewed official primary source records and at least one bounded obligation in the Registry.

Use `FOUNDATION_ONLY` when the jurisdiction is modeled but the source-backed obligation set has not been completed.

A pilot status does not mean exhaustive jurisdiction coverage.

## Freshness

Every source must have one matching source-status entry and one matching review-due entry.

Use shorter review intervals when:

- pending amendments are known;
- a law or provider policy is changing quickly;
- implementation dates are approaching;
- source availability or supersession risk is elevated.

If a review date is missed, the source must be refreshed or explicitly moved to `REVIEW_OVERDUE` according to the Registry validation contract.

## Validation

Before requesting merge, the exact proposed revision must pass the repository's `Registry Validation` workflow, including semantic Registry validation, official-source provenance validation, executable JSON Schema contracts, machine-record validation, regression tests, and deterministic validation-candidate construction.

Do not weaken validation, provenance, review, or authority boundaries to make a contribution pass.

Validation does not itself authorize merge or trusted publication.

## Publication

Merging a contribution to `main` does not publish a trusted Registry release. Trusted release construction and publication are separate governed actions described in `GOVERNANCE.md` and `docs/RELEASE_PACKAGING.md`.

## Security and sensitive information

Do not submit secrets, access tokens, private legal documents, confidential client material, personal data, or non-public organizational compliance evidence.

Registry records should rely on publicly verifiable official source material and reusable evidence definitions.
