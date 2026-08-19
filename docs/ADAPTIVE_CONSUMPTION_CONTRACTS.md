# Adaptive Registry Consumption Contracts (R5-R6)

## Status

Candidate contracts layered on the validated R1-R4 source-monitor head. They do not merge Registry PR #23, publish a trusted Registry release, interpret law, decide project applicability, or grant Orchestra execution authority.

## R5 Capability Manifest

`registry/capabilities.json` is a distributed JSON-first capability description. It declares versioned machine surfaces that a consumer may negotiate without parsing Markdown.

The manifest is descriptive only. Every authority-boundary flag is false.

Current capability IDs:

- `cap.query.v1`
- `cap.query.multi-jurisdiction.v1`
- `cap.query.scoped-freshness.v1`
- `cap.release-delta.v1`
- `cap.source-monitor.v1`
- `cap.schema-negotiation.v1`

Each entry identifies its contract version, required Registry records, optionality, and explicit fallback behavior.

## R6 Release Delta

`schema/release-delta.schema.json` defines the closed evidence contract.

`scripts/release_delta.py` compares two Registry repository or unpacked-bundle roots without network access. It emits exact base/target manifest identities, changed record types, affected capability/domain/jurisdiction/provider/source/obligation IDs, structural changes, a fail-closed disposition, and a stable digest.

Disposition meanings:

| Disposition | Meaning |
| --- | --- |
| `UNCHANGED` | No relevant Registry machine records changed |
| `COMPATIBLE_SCOPED_CHANGE` | Compatible additive/taxonomy change with bounded impact |
| `REVALIDATION_REQUIRED` | Freshness/currentness changed and affected consumers should revalidate |
| `UNSUPPORTED_CAPABILITY_CHANGE` | Capability removal or contract/status mutation may break consumers |
| `HUMAN_REVIEW_REQUIRED` | Source/obligation change or review-sensitive state requires governed human interpretation |

A release delta is evidence only. It cannot update obligations, approve applicability, merge a PR, publish a release, or expand downstream authority.

## Compatibility boundary

The current immutable `registry-v0.2.0` release predates R5-R6. Consumers must therefore support an explicit legacy compatibility profile for v0.2.0 rather than inventing capability metadata that is not present in that release.

Future releases may include `registry/capabilities.json` because the release builder packages the Registry directory. Publication remains separately authorized.
