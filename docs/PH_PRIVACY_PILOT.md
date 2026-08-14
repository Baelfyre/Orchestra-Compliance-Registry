# Philippines Privacy Source Pilot

## Purpose

This bounded pilot proves the source-backed registry lifecycle before broader multi-jurisdiction/provider population. It is compliance intelligence for Orchestra governance, not legal advice and not a project-specific compliance determination.

## Verification date

Primary-source verification was performed on **2026-08-14** against current National Privacy Commission publications.

## Source set

| Source ID | Primary authority source | Registry role |
| --- | --- | --- |
| `PH-DPA-RA10173` | `https://privacy.gov.ph/data-privacy-act/` | Statutory source text and general privacy principles |
| `PH-DPA-IRR-2016` | `https://privacy.gov.ph/implementing-rules-regulations-data-privacy-act-2012/` | Implementing-rule source text |
| `PH-NPC-CIRC-2023-06` | `https://privacy.gov.ph/wp-content/uploads/2024/03/NPC-Circular-Repeal-16-01-Signed.pdf` | Current security/privacy-engineering circular used for direct obligation locators |
| `PH-NPC-ADV-2025-02` | `https://privacy.gov.ph/wp-content/uploads/2025/12/NPC_Advisory2025-02.pdf` | Privacy-engineering lifecycle guidance; not treated as a standalone mandatory obligation without Governor review |

The current NPC issuance index also continues to list Circular 2023-06 and Advisory 2025-02. The NPC publication notice for Circular 2023-06 states that it expressly repealed Circular 16-01 and took effect on 2024-03-30.

## Initial obligation set

The pilot records six evidence-oriented obligation families sourced from NPC Circular 2023-06 and, where useful, the DPA/IRR or Advisory 2025-02:

1. Privacy Impact Assessment and material-change reassessment.
2. Privacy Management Program and periodic training.
3. Privacy-by-Design / Privacy-by-Default and privacy-engineering traceability.
4. Documented retention periods and periodic retention review.
5. Access-control and authentication controls for personal data.
6. Business-continuity planning, backup/restoration, and periodic testing.

Each obligation includes source IDs, section locators, jurisdiction/domain metadata, and examples of reviewable SDLC evidence. The evidence list is a traceability aid; it does not independently prove legal compliance.

## Freshness lifecycle

Every populated source must have exactly one matching entry in both:

- `registry/source-status.json`
- `registry/review-due.json`

The source record's embedded verification status must match the status ledger. When `next_review_due` is earlier than the validation date, validation fails unless the source is explicitly marked `REVIEW_OVERDUE`. This preserves stale evidence as a visible governance condition instead of silently treating it as current.

The daily `Registry Validation` workflow provides a recurring freshness check once this phase reaches canonical `main`.

## Applicability boundary

Registry records do not decide whether a particular project is a PIC, PIP, covered processing system, or otherwise subject to a specific duty. Governor owns applicability and material interpretation. Steward may translate Governor-qualified obligations into project requirements; Arbiter verifies continuity and evidence identity. Registry data never grants execution, release, deployment, destructive-operation, or policy-activation authority.

## Release boundary

This pilot remains `DRAFT` with `release_sequence: 0`. It is not a trusted registry release. Trusted release packaging, manifest hashing, immutable GitHub Release publication, and Orchestra sync/install validation are separate later phases.
