# Registry v0.2.0 Trusted Release Evidence

## Status

`registry-v0.2.0` is a published, non-draft, non-prerelease, immutable GitHub Release.

This document is the human-readable companion to `machine/release-evidence-v0.2.0.json`. The machine record is the structured repository evidence projection; the live immutable GitHub Release remains publication source reality and must be reverified before trust-sensitive mutation.

## Release identity

| Field | Verified value |
| --- | --- |
| Release tag | `registry-v0.2.0` |
| Registry version | `0.2.0` |
| Release sequence | `2` |
| Release ID | `373113025` |
| Published at | `2026-08-19T14:20:56Z` |
| Draft | `false` |
| Prerelease | `false` |
| Immutable | `true` |
| Source commit | `cb32038a2683eb2c19f52646892d3257996a06eb` |
| Source tree | `10ce7849fd5b95b3ca756eff213bb506d00a89de` |
| Publication workflow run | `32263446171`, attempt `1` |

Release URL:

`https://github.com/Baelfyre/Orchestra-Compliance-Registry/releases/tag/registry-v0.2.0`

## Integrity evidence

The release was built twice from the frozen source commit. Both builds were byte-identical before publication.

| Artifact | SHA-256 |
| --- | --- |
| `release-manifest.json` | `cb98e4496da8952cff1432207d57f04379364bac2e95cc422de173681a8fb2b4` |
| `orchestra-compliance-registry.zip` | `71414aaead10634c2a4b79ec519b4fc76fb32af71cd831ef48f2133bcc211388` |

Required release assets were verified before and after publication:

- `orchestra-compliance-registry.zip`
- `orchestra-compliance-registry.zip.sha256`
- `release-manifest.json`
- `release-manifest.sha256`

## Validation evidence

The publication workflow re-ran the exact canonical source validation before building the release:

- Registry semantic validation: PASS
- Official source provenance validation: PASS
- Executable JSON Schema contracts: PASS
- JSON-first machine records: PASS
- Full regression suite: PASS, 60 tests
- Deterministic build A/B comparison: PASS
- Exact tag target verification: PASS
- Draft release asset verification: PASS
- Published immutable release verification: PASS

The workflow completed successfully on run `32263446171`. The runtime-generated release evidence was also recorded in repository issue `#21`.

## Scope

This trusted release promotes the bounded international privacy pilot represented by the frozen canonical source tree. It includes source-backed pilot coverage for the Philippines, EU/EEA, Canada, Australia, and Singapore, with the United States and Mexico remaining `FOUNDATION_ONLY` pending separately reviewed source-backed modeling.

The release also includes the official-primary-source provenance model, structured citations, date provenance, compact human README, complete machine README index, freshness controls, and fail-closed validation added in the v0.2.0 source phase.

Provider/platform, broader software-development, cybersecurity, database/data-governance, and AI compliance coverage remains subsequent governed work and is not implied by this release.

## Trust boundary

- The immutable GitHub Release is publication source reality.
- The editable repository remains `0.2.0-dev.1` `DRAFT` source state with release sequence `0`.
- The release builder stages a `0.2.0` `TRUSTED_RELEASE` manifest with release sequence `2`; it does not rewrite editable source state.
- Release publication does not establish project-specific legal applicability or legal advice.
- Any future mutation or replacement requires live external re-verification and a separately governed transition.
