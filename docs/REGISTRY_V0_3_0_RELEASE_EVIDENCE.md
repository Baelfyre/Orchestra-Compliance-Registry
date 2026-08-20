# Registry v0.3.0 Release Evidence

`registry-v0.3.0` is the current trusted Orchestra Compliance Registry distribution.

## Publication state

| Field | Value |
| --- | --- |
| Trust state | `PUBLISHED_IMMUTABLE_VERIFIED` |
| Release ID | `373417769` |
| Release tag | `registry-v0.3.0` |
| Registry version | `0.3.0` |
| Release sequence | `3` |
| Published at | `2026-08-20T00:11:24Z` |
| Source commit | `20eb859db153f17e24c052a13765e982d51cedbf` |
| Source tree | `763be9062a0c23031c794403dc4592f5db4389b0` |
| Publication workflow | `32316311024` attempt `1` |
| Release evidence issue | `#28` |

The release is non-draft, non-prerelease, and GitHub reported it immutable after publication.

## Integrity

| Evidence | SHA-256 |
| --- | --- |
| Release manifest | `2674c7625188e20047274f3f3e7a25836299c640913bfc2eb20de2d4349808a9` |
| Registry bundle | `dc74b59f3c11dd7c740a91a4c6667064b84c3505d8bfc62382cd2ce0f4f0bfea` |

Required published assets:

- `orchestra-compliance-registry.zip`
- `orchestra-compliance-registry.zip.sha256`
- `release-manifest.json`
- `release-manifest.sha256`

The publication workflow rebuilt the release twice from the exact frozen source and required byte-identical outputs before creating the tag or GitHub Release.

## v0.3.0 scope

This release publishes the canonical Registry R1-R6 state that was jointly reconciled with Orchestra O1-O6:

- bounded official-source monitoring against a reviewed fingerprint baseline;
- six-hour source-monitor scheduling with evidence preservation;
- candidate-only automation when a source fingerprint may have changed or moved;
- R5 JSON-first capability manifest for deterministic consumer negotiation;
- R6 deterministic release-delta contract for scoped downstream revalidation;
- source-backed privacy pilot coverage for the Philippines, EU/EEA, Canada, Australia, and Singapore;
- official-primary-source provenance, structured citations, source dates, freshness ledgers, and human-governed applicability boundaries.

The release does not automatically interpret legal changes, rewrite obligations, determine project applicability, grant Orchestra execution authority, or authorize downstream deployment.

## Source and publication boundary

The editable repository remains `0.2.0-dev.1` / `DRAFT` / source sequence `0`. The deterministic release builder stages the trusted `0.3.0` / sequence `3` distribution without rewriting editable Registry records.

The immutable GitHub Release is publication source reality. Repository evidence files are machine/human projections and must be externally reverified before trust-sensitive mutation.
