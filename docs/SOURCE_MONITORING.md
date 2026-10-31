# Official Source Monitoring

## Purpose

The Registry is not static. Laws, regulations, regulator guidance, and provider/platform requirements can change after a Registry release is published. The source-monitor subsystem detects changes at the official primary-source boundary and produces deterministic evidence without silently deciding legal applicability or publishing a new trusted release.

## Authority boundary

The monitor may automatically:

- fetch canonical official primary sources or a bounded official dissemination representation of the same source;
- verify that redirects remain inside the declared source-specific official authority boundary;
- compute deterministic source fingerprints;
- compare live fingerprints with the reviewed baseline;
- classify unchanged, metadata-only, potential substantive change, source-moved, or source-unavailable states;
- preserve machine-readable source-watch evidence;
- create a bounded draft candidate pull request when a substantive change or source move is detected; and
- mark affected source status in that candidate branch for human interpretation.

The monitor must not automatically:

- determine that a legal duty applies to a particular project;
- create, remove, or rewrite compliance obligations from an observed web-page change;
- accept a new source baseline;
- merge its own candidate pull request;
- grant governance or execution authority; or
- publish a trusted Registry release.

## Schedule

The scheduled workflow is `.github/workflows/source-monitor.yml`. **All eight sources are now checked once daily at 04:23 Asia/Singapore**, instead of every six hours, because Singapore Statutes Online (SSO) permits automated extraction of Singapore legislation only between 03:00 and 07:00 Singapore Time. The policy `schedule_hours` is therefore 24. GitHub Actions schedules are polling, not authoritative source webhooks, and may be delayed; an external source change is detected on the next successful monitor run, not necessarily when published. This introduces a 24-hour monitoring cadence for the seven other sources as well. Restoring six-hour polling for those sources would require a separately reviewed source-aware scheduling design.

Pull requests use the same workflow in read-only bootstrap-preview mode. Outside the allowed SSO extraction window, they explicitly **defer** live verification and preserve a marker artifact instead of fetching SSO. A successful deferred PR job is NOT proof that the reviewed source baseline is current. During the window, a live preview still must validate all official sources. Manual `workflow_dispatch` outside the window fails before any source fetch. No PR job receives repository write permission.

## Machine contracts

| Record | Purpose |
| --- | --- |
| `machine/source-monitor-policy.json` | Canonical monitoring policy, cadence, strategies, and automation boundaries |
| `machine/source-monitor-baseline.v1.json` | Reviewed source fingerprints used for change comparison |
| `schema/source-monitor-policy.schema.json` | Closed policy contract |
| `schema/source-monitor-baseline.schema.json` | Closed baseline contract |
| `schema/source-watch-receipt.schema.json` | Closed evidence receipt contract |
| `scripts/source_monitor.py` | Deterministic fetch, fingerprint, comparison, and candidate application runtime |
| `scripts/source_monitor_live.py` | Source-specific live transport hardening for official authorities whose public presentation layer contains automation or moving-boilerplate behavior |

`machine/source-watch-candidate.json` is created only on an automated change-candidate branch and preserves the exact source-watch receipt that caused that candidate.

## Fingerprinting strategies

### HTML_NORMALIZED_TEXT

Used for official legislation and regulator pages served as HTML or XHTML. The monitor records both:

- a SHA-256 digest of the raw response bytes; and
- a SHA-256 digest of normalized visible text after removing script/style/template content and normalizing Unicode and whitespace.

If raw representation changes while normalized official text is unchanged, the result is `METADATA_ONLY`. If normalized text changes, the result is `POTENTIAL_SUBSTANTIVE_CHANGE`.

### BINARY_SHA256

Used for signed official PDFs and other binary primary sources. A binary digest change is classified as `POTENTIAL_SUBSTANTIVE_CHANGE` because a generic monitor cannot safely determine whether the PDF change is editorial, metadata-only, or legally substantive.

## Source-specific transport hardening

### EU-GDPR-2016-679

The canonical Registry identity remains the EUR-Lex Regulation (EU) 2016/679 source. For unattended monitoring, `scripts/source_monitor_live.py` retrieves the English CELEX representation through the European Union Publications Office Cellar XHTML dissemination surface because the public EUR-Lex presentation endpoints can return automation/challenge content instead of stable legal text.

The Cellar request begins on HTTPS at `publications.europa.eu`. If the official service emits a legacy HTTP-form Cellar resource identifier on that same authority, the monitor converts that identifier to HTTPS before following it. It never follows an HTTP request. Any redirect to another host or any non-HTTPS final representation fails closed. The returned representation must be `application/xhtml+xml` and must contain expected GDPR text sentinels before it can be fingerprinted.

This transport choice changes only how the monitor obtains a stable official representation. It does not change the Registry's canonical EUR-Lex source identity, legal interpretation, obligation records, or applicability decisions.

### SG-PDPA-2012
**Automated-access terms:** [SSO Terms of Use](https://sso.agc.gov.sg/Terms-of-Use), clause 15(d), and [SSO FAQ A3](https://sso.agc.gov.sg/FAQ) limit automated extraction to 03:00–07:00 Singapore Time, with non-intrusive and non-circumvention requirements. The source-specific transport checks that local window before issuing an SSO request. A request outside the window is deferred with a `SOURCE_UNAVAILABLE` receipt if invoked through the checking runtime, never treated as successful validation. Any future rate or access restriction remains binding even within that window. This is an automated-use condition, not proof that a past HTTP 202 response resulted specifically from timing. According to SSO FAQ B1, the SSO consolidation is **not the authoritative legislative text**; the Government Gazette is authoritative and must inform legal-effect review.


Singapore Statutes Online renders a moving `Current version as at DD Mon YYYY` status label in the page presentation. That daily display value is not part of the monitored statutory text, so the source-specific normalizer replaces only the date inside that exact status label with a fixed placeholder before computing the normalized-text digest.

The raw response SHA-256 is still preserved. Changes elsewhere in the normalized page remain detectable, and the monitor requires both expected PDPA text sentinels and the moving status label to be present. If those invariants disappear, the source fails closed rather than broadening normalization automatically.

## Failure diagnostics and incident de-duplication (2026-10-31)

For Singapore Statutes Online, a response that passes the HTTPS/content-type boundary but lacks readable statutory text is rejected. The receipt now records a bounded failure diagnostic (HTTP status, content type, response byte count, and raw SHA-256) without retaining raw challenge HTML or broadening text acceptance. This does not resolve an upstream transport restriction or prove the cause of a past response.

Each scheduled check still saves a unique source-watch receipt artifact. When one source fails, separately observed `POTENTIAL_SUBSTANTIVE_CHANGE` or `SOURCE_MOVED` results remain in the receipt and are now included in the incident issue notification. The overall state remains `MONITOR_FAILURE`, and the automated candidate-PR path remains disabled until a complete trustworthy check succeeds. No legal obligations or trusted-release state are mutated.

Repeated failures with the same sorted failure IDs, sorted actionable IDs, and candidate fingerprint produce the same incident signature. The issue reporter posts a new notification only when the signature changes, reducing six-hour duplicate comments. Repeated runs still fail visibly and preserve per-run evidence. The current classifier signature intentionally omits transient timestamps and raw HTTP error text; operators must consult receipt artifacts for those details.

See [2026-10-31 investigation and review gates](SOURCE_MONITOR_20261031_INVESTIGATION.md).

## Change states

| State | Meaning | Automatic repository action |
| --- | --- | --- |
| `UNCHANGED` | Reviewed fingerprint is unchanged | None |
| `METADATA_ONLY` | Raw representation or same-authority URL changed while normalized text remained stable | Evidence only |
| `POTENTIAL_SUBSTANTIVE_CHANGE` | Reviewed official text/binary fingerprint changed | Draft candidate PR; affected source marked `HUMAN_INTERPRETATION_REQUIRED` in candidate only |
| `SOURCE_MOVED` | Final URL left the declared official authority boundary | Draft candidate PR; affected source marked `SOURCE_MOVED` in candidate only |
| `SOURCE_UNAVAILABLE` | A trustworthy fetch could not complete | Monitor failure evidence and issue signal; no source-state mutation |

## Candidate deduplication

An actionable source set receives a deterministic candidate key derived only from source identity, change state, final URL, and current source fingerprints. Repeated scheduled checks against the same unreviewed external change therefore resolve to the same automation branch name instead of opening duplicate candidate pull requests.

## Baseline lifecycle

1. A bootstrap preview fetches all configured official sources.
2. The generated fingerprints are reviewed and committed as an `ACTIVE` baseline.
3. Scheduled checks compare live source state to that reviewed baseline.
4. A detected change opens a draft candidate PR but does not replace the baseline.
5. Human/Governor review re-reads the official source and determines source status, date semantics, supersession, applicability implications, and obligation impact.
6. Only the reviewed candidate may update the baseline as part of the governed Registry change.
7. Trusted publication remains a separate explicitly authorized release transition.

## Validation

The normal `Registry Validation` workflow validates the monitor policy and baseline without network access. `tests/test_source_monitor.py` covers normalization, classification, authority-boundary handling, configuration coverage, and fail-closed candidate status application. `tests/test_source_monitor_live.py` locks the source-specific HTTPS Cellar redirect rule and the narrow Singapore moving-date normalization rule without performing network access.

The separate `Registry Source Monitor` workflow exercises live official-source fetches and preserves the generated baseline or source-watch receipt as GitHub Actions evidence.
