# Source monitor investigation and remediation (2026-10-31)

Status: **PARTIAL_REMEDIATION_PENDING_LIVE_VALIDATION_AND_LEGAL_REVIEW**.
This document records evidence and proposed review work, not legal conclusions or an approved Registry source/baseline update.

## Run evidence

- Initial failure: https://github.com/Baelfyre/Orchestra-Compliance-Registry/actions/runs/40881163273
- Reproduced: https://github.com/Baelfyre/Orchestra-Compliance-Registry/actions/runs/41138462254
- Existing incident issue: https://github.com/Baelfyre/Orchestra-Compliance-Registry/issues/31
- Reviewed main commit: `2670f98a2fff5e154893c2dd64e14b520be7b104`.
- Both archived receipts: `MONITOR_FAILURE`; same actionable source digests and source classifications.
- Singapore `SG-PDPA-2012`: `SOURCE_UNAVAILABLE`, reason `normalized text is empty`.
- Australia `AU-PRIVACY-ACT-1988`: `POTENTIAL_SUBSTANTIVE_CHANGE`; current normalized SHA-256 `164a50126673266c8011e7ffbd1fa2c9b4612f769519ed965b34a36b27a89f65`.
- Canada `CA-PIPEDA-SC2000-C5`: `POTENTIAL_SUBSTANTIVE_CHANGE`; current normalized SHA-256 `c8ecac4758bc9d03877c7d6841f1ce92bef3b38cb0cc5928e75a0cc4ed3b1216`.
- Philippine DPA/IRR: `METADATA_ONLY`; EU GDPR and two Philippine NPC PDFs: `UNCHANGED`.

The receipts do not preserve raw HTML, so the exact Singapore response cannot be reconstructed.
The failed fetch had passed the response processing path far enough to attempt HTML normalization.
A script-only page, access challenge, or unexpected response are hypotheses, **not confirmed root causes**.
Independent HTTP retrieval of the SSO root path also encountered an HTTP 403 in a separate retrieval environment. This does not establish what the GitHub runner actually received.

## Official-primary-source review leads

| Source | Official evidence inspected | Classification and next step |
| --- | --- | --- |
| Singapore PDPA | https://sso.agc.gov.sg/Act/PDPA2012?ProvIds=P19B- (version timeline lists amendment by Act 2 of 2026 on 16 Oct 2026) | **Verified history event, legal impact unreviewed**. Compare affected provisions against Registry references (especially sections 24 and 25), verify text and commencement, then determine applicability under human/Governor review. The current Registry record still reflects 2025-12-05 and must not be silently updated. |
| Australia Privacy Act | https://www.legislation.gov.au/C2004A03712/latest/text (compilation C2026C00227 C104, 04 June 2026, same compilation identity as reviewed baseline) | **Digest change not established as statutory change**. Compare actual provision text or stable official compilation representation with reviewed snapshot before updating status or baseline. |
| Canada PIPEDA | https://laws-lois.justice.gc.ca/eng/acts/P-8.6/ (consolidation current to 2026-09-30; last amended 2025-03-04); https://lois.justice.gc.ca/eng/acts/p-8.6/nifnev.html (amendments not in force include 2026, c.3, s.389) | **Digest change not established as an in-force statutory change**. Separate moving consolidation date, pending amendments, and any actual legal-text changes before human interpretation. |

Official webpages are live and can change. The above observations are time-bounded and do not replace a signed review of exact texts or legally effective dates.

## P0-P2 implementation scope

1. **P0 response diagnostics**: on rejected Singapore HTML content, record only response status, content type, byte count, and raw SHA-256 in the source-watch receipt's reason string. Preserve strict HTTPS host boundary, required legal-text sentinels, and fail-closed behavior. Do not attempt CAPTCHA evasion or accept script-only/non-statutory content.
2. **P0 legal review evidence**: this investigation records the 2026 Singapore timeline event as a proposed review item; no source metadata, obligations, or baseline accepted automatically.
3. **P1 partial evidence**: for an overall `MONITOR_FAILURE`, include independently observed actionable IDs and candidate fingerprint in a failure issue report and retain the per-run receipt artifact. Do **not** auto-create an actionable PR while source verification is incomplete.
4. **P2 de-duplication**: compute a stable report signature from sorted failure IDs, sorted actionable IDs and candidate key. Only comment when the signature changes. Each 6-hour run still retains its own receipt and fails visibly. A resolved/changed incident must not be marked successful without a valid full check.
5. **Tests**: synthetic script-only SSO response, missing text sentinel, stable/change report fingerprint, notification de-duplication, invalid receipt fail-closed, and CLI behavior.

## Human approval gates

- Compare exact authoritative provision text, legislative history, in-force dates, and source applicability.
- Accept or reject each Australian, Canadian, and Singapore source change.
- Approve any reviewed source metadata, obligation, or baseline revision.
- Review live hosted execution (including the new response diagnostics); determine whether an approved stable official Singapore representation exists.
- Keep PR in draft until acceptance tests and governance checks satisfy the repository rules. No automated merge, release, or policy relaxation.
