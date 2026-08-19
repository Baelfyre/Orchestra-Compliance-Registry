# International Privacy Pilot

## Purpose

The international privacy pilot extends the Registry beyond its original Philippine source-backed dataset without claiming exhaustive global compliance coverage.

The pilot is designed to prove that the Registry can represent multiple legal systems while preserving the same source identity, freshness, evidence, applicability, and publication boundaries used by the original Philippine pilot.

## Coverage states

Jurisdictions use two explicit Registry maturity states:

- `SOURCE_BACKED_PILOT`: at least one reviewed primary authority source and at least one bounded evidence-oriented obligation are present in the editable Registry.
- `FOUNDATION_ONLY`: the jurisdiction is modeled for future expansion, but the Registry does not assert a source-backed obligation set for it.

These states describe Registry content maturity only. They do not establish legal applicability, completeness, legal advice, or compliance certification.

## Source-backed jurisdictions

### Philippines

The original source-backed pilot remains in place and is documented separately in `PH_PRIVACY_PILOT.md`.

### EU / EEA

Primary source:

- Regulation (EU) 2016/679, General Data Protection Regulation
- https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679

Initial obligation slice:

- Article 25: data protection by design and by default;
- Article 32: security of processing;
- Article 35: data protection impact assessment for likely high-risk processing.

The Registry does not infer territorial scope, controller/processor role, Member State derogations, sectoral rules, or project applicability.

### Canada

Primary source:

- Personal Information Protection and Electronic Documents Act (PIPEDA)
- https://laws-lois.justice.gc.ca/eng/acts/P-8.6/

Initial obligation slice:

- Schedule 1 Clause 4.1: accountability;
- Schedule 1 Clause 4.7: safeguards.

The source is tracked as `CURRENT_WITH_PENDING_CHANGE` because the official Justice Laws publication identifies amendments that are not yet in force. The Registry does not infer commercial-activity scope, federal/provincial division, substantially similar provincial law, or project applicability.

### Australia

Primary source:

- Privacy Act 1988
- https://www.legislation.gov.au/C2004A03712/latest/text

Initial obligation slice:

- Australian Privacy Principle 1: open and transparent management of personal information;
- Australian Privacy Principle 11: security of personal information and destruction or de-identification when the statutory conditions are met.

The Registry does not infer APP-entity status, statutory exemptions, state or territory overlap, sector-specific duties, or project applicability.

### Singapore

Primary source:

- Personal Data Protection Act 2012
- https://sso.agc.gov.sg/Act/PDPA2012

Initial obligation slice:

- Section 24: protection of personal data;
- Section 25: retention limitation.

The Registry does not infer whether a particular entity is an organisation within scope, whether an exemption applies, whether sectoral legislation changes the analysis, or whether an obligation applies to a project.

## Foundation-only jurisdictions

### United States

The US remains `FOUNDATION_ONLY` in this pilot. A useful US model requires explicit treatment of federal requirements, state privacy laws, sector-specific regimes, effective dates, thresholds, and subjurisdiction applicability. The Registry will not represent that complexity as one generic national privacy obligation set.

### Mexico

Mexico remains `FOUNDATION_ONLY` in this pilot. Primary-source review and a bounded obligation set must be completed before the jurisdiction can move to `SOURCE_BACKED_PILOT`.

## Canonical record rules

A jurisdiction should not move from `FOUNDATION_ONLY` to `SOURCE_BACKED_PILOT` unless the proposed change includes all required machine records and passes Registry Validation.

At minimum, a source-backed jurisdiction slice requires:

1. A primary authority source in `registry/sources.json`.
2. A matching source-status entry in `registry/source-status.json`.
3. A matching freshness schedule in `registry/review-due.json`.
4. At least one obligation in `registry/obligations.json` with a direct source locator.
5. A jurisdiction entry marked `SOURCE_BACKED_PILOT`.
6. Updated manifest counts.
7. Regression coverage proving the source-backed jurisdiction is not an empty label.

## Evidence-oriented obligations

Obligations are intended to help software and governance workflows identify evidence that may be relevant to a legal or regulatory duty. They are not automatic legal conclusions.

Each obligation therefore preserves:

- source identity;
- jurisdiction identity;
- a direct source locator;
- a bounded summary;
- suggested evidence artifacts;
- an interpretation state requiring Governor applicability review.

The Registry must not convert a source into project-specific legal advice, determine legal scope automatically, or authorize execution based solely on a matched obligation.

## Expansion strategy

Future expansion should proceed in small, reviewable slices. Useful next candidates include:

- US state and federal privacy modeling;
- Canadian provincial privacy overlap;
- additional Asia-Pacific privacy regimes;
- United Kingdom privacy/data-protection sources as a distinct jurisdictional framework;
- accessibility requirements;
- security standards and regulatory security obligations;
- platform and distribution-provider requirements.

Breadth should not be achieved by weakening provenance, source freshness, applicability review, or release trust boundaries.

## Publication boundary

The international pilot is editable `DRAFT` source state. It does not modify the immutable `registry-v0.1.0` trusted release.

A future international trusted release requires its own validated deterministic candidate, governed publication decision, immutable release assets, and independent verification.
