# Contributing to Orchestra Compliance Registry

Thank you for helping expand the Registry.

This repository accepts source-backed proposals for jurisdictions, obligations, providers, standards, source-status updates, and supporting validation. Contributions must preserve the Registry's provenance, applicability, freshness, and publication boundaries.

## Before contributing

Read:

- `README.md` for current coverage and trust boundaries;
- `GOVERNANCE.md` for the canonical change path and authority model;
- `docs/INTERNATIONAL_PRIVACY_PILOT.md` for the current jurisdiction expansion model;
- `registry/manifest.json` for the machine record map.

## Preferred contribution unit

Keep a pull request bounded to one reviewable jurisdiction, source family, provider, or maintenance objective whenever practical.

A new source-backed jurisdiction slice should normally include:

1. A primary authority record in `registry/sources.json`.
2. One or more evidence-oriented obligations in `registry/obligations.json`.
3. A matching entry in `registry/source-status.json`.
4. A matching review schedule in `registry/review-due.json`.
5. The jurisdiction coverage state in `registry/jurisdictions.json`.
6. Updated `registry/manifest.json` counts.
7. Tests or validation changes needed to preserve the fail-closed contract.
8. Human documentation describing scope and known exclusions when the slice materially expands coverage.

## Source requirements

Canonical legal and regulatory records should use primary authority sources whenever available. Examples include official legislation databases, official regulators, government publications, and signed regulatory instruments.

A contribution should identify:

- stable source ID;
- official title;
- source type;
- issuing authority;
- canonical HTTPS source URL;
- jurisdiction IDs;
- relevant domains;
- current verification status and date;
- direct section, article, schedule, or equivalent locator for each obligation;
- an explicit interpretation boundary.

Secondary summaries, blogs, search snippets, AI-generated explanations, and commercial compliance pages may help locate a primary source but should not replace primary authority verification in canonical records.

## Obligation writing rules

Obligations should be evidence-oriented and source-bound.

Do:

- summarize the reviewed legal or regulatory text narrowly;
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

Use `SOURCE_BACKED_PILOT` only when the jurisdiction has reviewed primary source records and at least one bounded obligation in the Registry.

Use `FOUNDATION_ONLY` when the jurisdiction is modeled but the source-backed obligation set has not been completed.

A pilot status does not mean exhaustive jurisdiction coverage.

## Freshness

Every source must have one matching source-status entry and one matching review-due entry.

Use shorter review intervals when:

- pending amendments are known;
- a law is changing quickly;
- implementation dates are approaching;
- source availability or supersession risk is elevated.

If a review date is missed, the source must be refreshed or explicitly moved to `REVIEW_OVERDUE` according to the Registry validation contract.

## Validation

Before requesting merge, run the repository validation commands documented by the project and ensure the complete test suite passes.

Do not weaken validation, provenance, review, or authority boundaries to make a contribution pass.

## Publication

Merging a contribution to `main` does not publish a trusted Registry release. Trusted release construction and publication are separate governed actions described in `GOVERNANCE.md` and `docs/RELEASE_PACKAGING.md`.

## Security and sensitive information

Do not submit secrets, access tokens, private legal documents, confidential client material, personal data, or non-public organizational compliance evidence.

Registry records should rely on publicly verifiable source material and reusable evidence definitions.
