# Trusted Release Packaging

## Purpose

Registry source state and Registry distribution state are separate trust boundaries. Canonical `registry/` content can be valid and reviewable while still remaining `DRAFT`. A trusted distribution candidate is built from that validated draft state without rewriting canonical source files in place.

`scripts/build_release.py` provides deterministic **candidate packaging only**. It does not create a tag, GitHub Release, marketplace publication, or policy activation.

## Candidate identity

A release candidate requires three explicit values:

- `registry_version` — a safe version token such as `0.1.0`
- `release_sequence` — a positive monotonic integer such as `1`
- `release_tag` — exactly `registry-v{registry_version}`, for example `registry-v0.1.0`

The source registry must still be canonical `DRAFT` state with `release_sequence: 0`. The builder copies the Registry into a temporary staging area, changes only the staged release identity to `TRUSTED_RELEASE`, and runs the semantic Registry validator again before packaging.

## Build command

```bash
python scripts/build_release.py \
  --output-dir artifacts/release-candidate \
  --registry-version 0.1.0 \
  --release-sequence 1 \
  --release-tag registry-v0.1.0
```

The command produces:

- `orchestra-compliance-registry.zip`
- `orchestra-compliance-registry.zip.sha256`
- `release-manifest.json`
- `release-manifest.sha256`

## Release manifest

The root `release-manifest.json` records:

- schema version
- canonical repository identity
- Registry version
- release sequence
- release tag
- `TRUSTED_RELEASE` distribution state
- exact SHA-256 for every bundled `registry/` file

`release-manifest.json` is intentionally outside its own `files` map. Orchestra validates the manifest separately and then requires the actual bundled file inventory to match the manifest exactly: missing files, unlisted files, changed hashes, path escapes, or identity mismatches fail closed.

## Determinism

The ZIP member order, member timestamp, permissions, compression settings, and JSON serialization used for the release manifest are fixed. Two builds from identical Registry input and identical release identity must produce byte-identical ZIP files and identical SHA-256 values.

This property is regression-tested. It makes the candidate reviewable and reproducible; it does **not** by itself establish trusted provenance.

## Content integrity versus distribution provenance

The bundle's internal SHA-256 map proves content integrity relative to its release manifest. It does not prove who published the bundle or whether it came from the canonical repository.

Normal Orchestra network synchronization requires a non-draft, non-prerelease, immutable GitHub Release in `Baelfyre/Orchestra-Compliance-Registry`. Local or air-gapped installation requires the expected `release-manifest.sha256` value to be obtained independently and supplied as an out-of-band trust anchor.

A self-consistent ZIP copied from an arbitrary branch is therefore still not a trusted Registry distribution.

## Publication gate

Candidate packaging may run in CI before publication. Publication remains a separately governed transition and must verify at minimum:

1. canonical Registry source state is merged through the protected review path;
2. exact canonical source validation is green;
3. release identity is monotonic and does not collide with an existing release;
4. the candidate is reproducible from the exact canonical source state;
5. the independently readable release-manifest SHA-256 is recorded;
6. the GitHub Release is non-draft, non-prerelease, immutable, and belongs to the canonical Registry repository;
7. Orchestra end-to-end sync/install/pinning/freshness behavior is validated against that trusted release boundary.

Validation or successful candidate construction does not independently authorize publication.
