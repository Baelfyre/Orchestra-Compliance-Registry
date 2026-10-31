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

## Hosted PR validation follow-up (2026-10-31)

- PR preview run https://github.com/Baelfyre/Orchestra-Compliance-Registry/actions/runs/41245449547 returned `SOURCE_MONITOR_FAIL` for Singapore with **HTTP status 202**, `text/html`, 2,399 response bytes, and raw SHA-256 `f37b0a7d527074f44aaccbeabe8d4b7a0c92a970788aedbd41aec5ff5a15acaf`. This establishes the observed transport status but **not** why the official server served it. The response must not be accepted as statutory text.
- PR Registry Validation https://github.com/Baelfyre/Orchestra-Compliance-Registry/actions/runs/41245449592 initially failed on an overdue Australian source review. The checked-in `review-due.json` shows **four** due dates of 2026-10-18 (NPC Advisory 2025-02, Canada PIPEDA, Australia Privacy Act, Singapore PDPA).
- A conservative draft-only correction marks those four source verification and ledger statuses `REVIEW_OVERDUE`, retains 2026-08-19 as the last actually accepted review date, and leaves all due dates unchanged. This removes false assertions of currentness without purporting to complete substantive legal review. Human review is required before merging or restoring reviewed-current statuses.
- The monitor now explicitly rejects non-200 Singapore responses, retaining SHA-256-only diagnostics. A 200 HTML response with no extractable statutory text also remains rejected.

## Official-primary-source review leads

| Source | Official evidence inspected | Classification and next step |
| --- | --- | --- |
| Singapore PDPA | https://sso.agc.gov.sg/Act/PDPA2012?ProvIds=P19B- (version timeline lists amendment by Act 2 of 2026 on 16 Oct 2026) | **Verified history event, legal impact unreviewed**. Compare affected provisions against Registry references (especially sections 24 and 25), verify text and commencement, then determine applicability under human/Governor review. The current Registry record still reflects 2025-12-05 and must not be silently updated. |
| Australia Privacy Act | https://www.legislation.gov.au/C2004A03712/latest/text (compilation C2026C00227 C104, 04 June 2026, same compilation identity as reviewed baseline) | **Digest change not established as statutory change**. Compare actual provision text or stable official compilation representation with reviewed snapshot before updating status or baseline. |
| Canada PIPEDA | https://laws-lois.justice.gc.ca/eng/acts/P-8.6/ (consolidation current to 2026-09-30; last amended 2025-03-04); https://lois.justice.gc.ca/eng/acts/p-8.6/nifnev.html (amendments not in force include 2026, c.3, s.389) | **Digest change not established as an in-force statutory change**. Separate moving consolidation date, pending amendments, and any actual legal-text changes before human interpretation. |

Official webpages are live and can change. The above observations are time-bounded and do not replace a signed review of exact texts or legally effective dates.

## Confirmed upstream automated-use restriction (2026-10-31)

- The [SSO Terms of Use](https://sso.agc.gov.sg/Terms-of-Use), clause 15(d), and [FAQ A3](https://sso.agc.gov.sg/FAQ) explicitly restrict automated extraction of Singapore legislation to **03:00–07:00 Singapore Time**, forbid deceptive/intrusive requests and circumvention of security measures. This was not accounted for in the original six-hour schedule.
- The previously configured `23 */6 * * *` UTC schedule executed at **01:23, 07:23, 13:23 and 19:23 SGT**; all four are outside the allowed window. Observed HTTP 202 does not itself prove timing-based blocking.
- To keep the current all-or-nothing eight-source check intact, the draft changes the schedule to **04:23 Asia/Singapore once per day** and records a policy cadence of 24 hours. This is a **tradeoff**, reducing freshness for the other seven sources from every six hours to daily. Source-separated workflows would allow different cadences but require additional design and human review.
- The Singapore fetch adapter now rejects out-of-window calls before making an HTTP request. Pull-request preview outside the window records a transparent **DEFERRED, NOT VERIFIED** artifact, and manual dispatch outside the window fails without fetching. Live in-window success remains unqualified until observed in hosted CI.
- SSO FAQ B1 states the SSO consolidation is not the authoritative statute text; use the official Government Gazette for final legal text and commencement review. Do not substitute a third-party aggregation site for official source evidence.

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
