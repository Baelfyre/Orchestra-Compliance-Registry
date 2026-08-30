# Registry v0.4.0 Release Evidence

## Status

`PUBLISHED_IMMUTABLE_VERIFIED`

This document is the human-readable companion to `machine/release-evidence-v0.4.0.json`. The machine record and live immutable GitHub Release are the authoritative publication evidence surfaces for exact identity checks. This document does not grant publication, legal, merge, execution, or applicability authority.

## Immutable release identity

| Field | Value |
| --- | --- |
| Release tag | `registry-v0.4.0` |
| Registry version | `0.4.0` |
| Release sequence | `4` |
| Release ID | `378292109` |
| Published at | `2026-08-28T06:15:24Z` |
| Source commit | `488c979b37dd84d8645fd8e6c288d297375c4e5b` |
| Source tree | `0d3bbf34ec7ab7e4833fba225aba96b829de1cec` |
| Draft | `false` |
| Prerelease | `false` |
| Immutable | `true` |
| Publication workflow run | `33147297345` attempt `1` |
| Workflow trigger commit | `76995bad2226824b3c17e8542deeb3137f4e43ee` |
| Release-evidence issue | `#36` |

Release URL: `https://github.com/Baelfyre/Orchestra-Compliance-Registry/releases/tag/registry-v0.4.0`

## Integrity evidence

| Artifact | SHA-256 |
| --- | --- |
| Release manifest | `040d6576cf10e9f7e3a9a051792869541c1d33b7af3c665fad8eecb939c7baaa` |
| Registry bundle | `e0457a75837d169d7bb8a7da14d8f4141d35a691952ff8f8978ef793e3cf92d3` |

Required immutable release assets:

- `orchestra-compliance-registry.zip`
- `orchestra-compliance-registry.zip.sha256`
- `release-manifest.json`
- `release-manifest.sha256`

## R7 / Orchestra O7.7 reconciliation

The trusted `registry-v0.4.0` release is the R7 publication boundary. Canonical Orchestra subsequently recorded the Registry dependency at commit `4926a3b5f48122dd45f3c8e83a12b8d071dd5387`, declared O7.7 `CANONICAL_MERGED_VERIFIED`, and recorded the latest joint-conformance evidence as `PASS` with `joint_r7_o7_conformance_complete = true`.

Registry reconciliation therefore records R7 as terminally implemented and validated against the trusted v0.4.0 publication while preserving these boundaries:

- canonical `registry/*.json` remains Registry authority;
- the local R7 index remains a derived disposable cache;
- MCP remains read-only transport;
- AI output remains non-authoritative interpretation/projection;
- legal interpretation and project applicability remain human-governed;
- validation and this evidence record do not grant release, merge, execution, or mutation authority.

## Editable source boundary

The editable source manifest remains intentionally separate at `0.2.0-dev.1`, release sequence `0`, status `DRAFT`. Trusted publication does not rewrite editable Registry source identity.

## Reverification rule

Live GitHub release, tag, asset, and repository identities must be reverified before any future trust-sensitive mutation. Historical evidence in this repository is not a substitute for live external verification.
