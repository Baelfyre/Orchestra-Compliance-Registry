# Source Provenance Audit

**Audit date:** 2026-08-19  
**Scope:** Eight source records and fifteen bounded obligations in the international privacy pilot  
**Authority rule:** Canonical Registry sources must be official primary sources published by the issuing government, regulator, supranational authority, company/provider, or standards body.

## Source policy

The Registry does not use Wikipedia, social media, community posts, blogs, aggregators, or secondary legal summaries as canonical evidence when the issuing authority publishes the source directly.

For government and regulatory material, the canonical URL must resolve to the issuing government, regulator, or official legislation service. For provider/platform material, the canonical URL must resolve to that provider's official developer, policy, legal, security, compliance, or documentation site. Secondary material may assist discovery but cannot replace the official source in a canonical Registry record.

Each canonical source record carries a structured citation, source identifier, direct official URL, source locator, date provenance, gathering date, verification date, and review cadence. Missing legal dates are left unset when the official source reviewed does not support an exact value.

## Date semantics

| Field | Meaning |
| --- | --- |
| `issued_date` | Assent, promulgation, adoption, signature, or issuance date stated by the official source |
| `publication_date` | Official publication date where distinct |
| `effective_date` | Entry into force or commencement date where established by the official source |
| `applicable_date` | Date the relevant provisions became applicable where distinct from entry into force |
| `current_text_as_of` | Date/version of the official consolidated text reviewed |
| `last_amended_date` | Latest amendment date stated by the official source |
| `gathered_at` | Date the source was retrieved for this Registry audit |
| `verification.verified_at` | Date source identity/currentness was rechecked |

## Audited sources

| Source | Official authority | Date references captured | Audit result | Official source |
| --- | --- | --- | --- | --- |
| `PH-DPA-RA10173` | National Privacy Commission, Philippines | Approved 2012-08-15; gathered/verified 2026-08-19. Exact effectivity is not inferred because the reviewed NPC text states only the 15-days-after-publication rule. | Verified official primary source | https://privacy.gov.ph/data-privacy-act/ |
| `PH-DPA-IRR-2016` | National Privacy Commission, Philippines | Promulgated 2016-08-24; gathered/verified 2026-08-19. Exact effectivity is not inferred without the official publication date. | Verified official primary source | https://privacy.gov.ph/implementing-rules-regulations-data-privacy-act-2012/ |
| `PH-NPC-CIRC-2023-06` | National Privacy Commission, Philippines | Issued 2023-12-01; effective 2024-03-30; gathered/verified 2026-08-19. | Verified official signed circular and issuance status | https://privacy.gov.ph/wp-content/uploads/2024/03/NPC-Circular-Repeal-16-01-Signed.pdf |
| `PH-NPC-ADV-2025-02` | National Privacy Commission, Philippines | Issued 2025-08-27; gathered/verified 2026-08-19. | Verified official signed advisory; guidance, not independently represented as statute | https://privacy.gov.ph/wp-content/uploads/2025/12/NPC_Advisory2025-02.pdf |
| `EU-GDPR-2016-679` | European Union / EUR-Lex | Signed 2016-04-27; OJ publication 2016-05-04; entry into force 2016-05-24; applicable 2018-05-25; gathered/verified 2026-08-19. | Verified official regulation; prior date semantics corrected | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679 |
| `CA-PIPEDA-SC2000-C5` | Department of Justice Canada / Justice Laws | Part 1 in force 2001-01-01; current text to 2026-06-14; last amended 2025-03-04; gathered/verified 2026-08-19. | Current official consolidated statute with amendments not yet in force tracked separately | https://laws-lois.justice.gc.ca/eng/acts/P-8.6/ |
| `AU-PRIVACY-ACT-1988` | Federal Register of Legislation, Australia | Assent 1988-12-14; commencement 1989-01-01; current compilation C104 effective 2026-06-04; gathered/verified 2026-08-19. | Verified latest official in-force compilation | https://www.legislation.gov.au/C2004A03712/latest/text |
| `SG-PDPA-2012` | Singapore Statutes Online / Attorney-General's Chambers | Acts Supplement publication 2012-12-03; principal Parts III-VII commenced 2014-07-02; current text reviewed as at 2026-08-07; latest timeline amendment 2025-12-05; gathered/verified 2026-08-19. | Verified official current text and legislative history | https://sso.agc.gov.sg/Act/PDPA2012 |

## Obligation recheck

The fifteen current pilot obligations were rechecked against the official legal text and direct locators. No substantive obligation summary required correction in this rerun. The checked areas are:

- Philippines: privacy impact assessment, privacy management program, privacy by design/default, retention, access control, and business continuity.
- EU/EEA: GDPR Article 25 data protection by design/default, Article 32 security of processing, and Article 35 DPIA.
- Canada: PIPEDA accountability and safeguards under section 5(1) and Schedule 1 clauses 4.1 and 4.7.
- Australia: Australian Privacy Principle 1 and Australian Privacy Principle 11.
- Singapore: PDPA sections 24 and 25.

The rerun identified a **metadata/date correction** for GDPR: 2018-05-25 is the application date, not the entry-into-force date. The Registry now records entry into force as 2016-05-24 and application from 2018-05-25.

## Interpretation boundaries retained

This audit verifies source identity, date provenance, currentness, and the textual basis for the bounded obligation records. It does not determine whether a law applies to a particular organization, user, product, sector, processing activity, deployment region, or contractual relationship. Those determinations remain governed applicability decisions.

A provider or platform rule may be contractually mandatory for distribution or service use without being legislation. A government or standards framework may be highly relevant without itself imposing a binding legal duty. Future provider and cross-domain records must preserve these distinctions.

## Machine companion

The machine-readable audit record is [`machine/source-provenance-audit.v1.json`](../machine/source-provenance-audit.v1.json). Canonical source details remain in [`registry/sources.json`](../registry/sources.json); the audit record is evidence of the 2026-08-19 rerun and does not replace Registry source authority.
