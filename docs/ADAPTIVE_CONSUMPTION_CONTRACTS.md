# Adaptive Registry Consumption Contracts (R5-R6)

## Status

R5-R6 are canonical on Registry `main` as part of the reconciled R1-R6 implementation at commit `be297335b55aa6a3a88a473c7e7da28614e95cd2` / tree `09df80b2bb26929cb1bdc1a641131bf68ef0b212`. The interface was reconciled against canonical Orchestra O1-O6 at `955a4b4918e28638a50e9564d1e3ea0127ae5f73`; the Registry capability manifest and Orchestra's frozen R5 fixture share Git blob SHA `978c1a6eecffe802df79e6d110a16b780ec6bd3f`.

Canonical implementation does not mean trusted publication. The immutable trusted Registry release remains `registry-v0.2.0`, which predates R5-R6. No new trusted release is published by this state reconciliation. These contracts do not interpret law, decide project applicability, grant Orchestra execution authority, or authorize automatic merge/release behavior.

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

Future trusted releases may include `registry/capabilities.json` because the release builder packages the Registry directory. Publication remains separately authorized and must be validated against the exact release candidate.
