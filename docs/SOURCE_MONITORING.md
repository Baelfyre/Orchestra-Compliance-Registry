# Official Source Monitoring

## Purpose

The Registry is not static. Laws, regulations, regulator guidance, and provider/platform requirements can change after a Registry release is published. The source-monitor subsystem detects changes at the official primary-source boundary and produces deterministic evidence without silently deciding legal applicability or publishing a new trusted release.

## Authority boundary

The monitor may automatically:

- fetch canonical official primary sources;
- verify that redirects remain inside the declared authority domain;
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

The scheduled workflow is `.github/workflows/source-monitor.yml` and is configured to run every six hours. GitHub Actions schedules are polling, not authoritative source webhooks, so an external source change is detected on the next successful monitor run rather than at the exact instant the publisher changes it.

Pull requests use the same workflow in read-only bootstrap-preview mode. The PR job fetches the official sources and produces a current baseline artifact but has no repository write permission.

## Machine contracts

| Record | Purpose |
| --- | --- |
| `machine/source-monitor-policy.json` | Canonical monitoring policy, cadence, strategies, and automation boundaries |
| `machine/source-monitor-baseline.v1.json` | Reviewed source fingerprints used for change comparison |
| `schema/source-monitor-policy.schema.json` | Closed policy contract |
| `schema/source-monitor-baseline.schema.json` | Closed baseline contract |
| `schema/source-watch-receipt.schema.json` | Closed evidence receipt contract |
| `scripts/source_monitor.py` | Deterministic fetch, fingerprint, comparison, and candidate application runtime |

`machine/source-watch-candidate.json` is created only on an automated change-candidate branch and preserves the exact source-watch receipt that caused that candidate.

## Fingerprinting strategies

### HTML_NORMALIZED_TEXT

Used for official legislation and regulator pages served as HTML. The monitor records both:

- a SHA-256 digest of the raw response bytes; and
- a SHA-256 digest of normalized visible HTML text after removing script/style/template content and normalizing Unicode and whitespace.

If raw representation changes while normalized official text is unchanged, the result is `METADATA_ONLY`. If normalized text changes, the result is `POTENTIAL_SUBSTANTIVE_CHANGE`.

### BINARY_SHA256

Used for signed official PDFs and other binary primary sources. A binary digest change is classified as `POTENTIAL_SUBSTANTIVE_CHANGE` because a generic monitor cannot safely determine whether the PDF change is editorial, metadata-only, or legally substantive.

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

The normal `Registry Validation` workflow validates the monitor policy and baseline without network access. `tests/test_source_monitor.py` covers normalization, classification, authority-boundary handling, configuration coverage, and fail-closed candidate status application.

The separate `Registry Source Monitor` workflow exercises live official-source fetches and preserves the generated baseline or source-watch receipt as GitHub Actions evidence.
