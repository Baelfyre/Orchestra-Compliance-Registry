# Registry v0.1.0 Release Readiness

## Status

`CANDIDATE_READY_PUBLICATION_NOT_AUTHORIZED`

This document records the release-readiness state for the first trusted Orchestra Compliance Registry distribution. It does not create a tag, GitHub Release, policy activation, deployment, or Orchestra publication authority.

## Canonical source baseline

- Repository: `Baelfyre/Orchestra-Compliance-Registry`
- Canonical branch: `main`
- Source commit: `6f802f0c32d20fe4ad0e7c8eb3a23f6b883341ac`
- Source state: `DRAFT`
- Source registry version: `0.1.0-dev.2`
- Source release sequence: `0`
- Registry Validation run: `31798524249`
- Semantic validation: `REGISTRY_VALID`
- Regression tests: `16 PASS`

The source Registry intentionally remains `DRAFT`. Trusted distribution identity is applied only to the deterministic staged candidate by `scripts/build_release.py`.

## Candidate identity

- Registry version: `0.1.0`
- Release sequence: `1`
- Release tag: `registry-v0.1.0`
- Asset: `orchestra-compliance-registry.zip`
- File count: `7`
- Release-manifest SHA-256: `9922ddcce77dfac0c01cac80fe6669aaffe37636826a56a4b54a8312558ee2d1`
- ZIP SHA-256: `b64889933d30a8dea27bcbbb95c952e4f053c14a4f345e1e04b27777b5025ec0`

Independent original and canonical replay builds produced the same candidate hashes. The deterministic-build regression also verifies byte-identical output from identical source state and release identity.

## Freshness state at readiness review

All four pilot sources are recorded `VERIFIED_CURRENT` with `checked_at: 2026-08-14`.

Review deadlines:

- `PH-DPA-RA10173`: 2026-11-12
- `PH-DPA-IRR-2016`: 2026-11-12
- `PH-NPC-CIRC-2023-06`: 2026-11-12
- `PH-NPC-ADV-2025-02`: 2026-10-13

Registry validation runs daily and fails closed if a current source passes its review deadline without an explicit state transition such as `REVIEW_OVERDUE`.

## Governance enforcement

Canonical `main` is governed by the active `compliance-ruleset`:

- pull request required;
- Squash-only merge;
- `validate-registry` required from GitHub Actions;
- required check must be current with the target branch;
- unresolved conversations block merge;
- force pushes blocked;
- branch deletion blocked;
- bypass list empty.

The solo-maintainer configuration intentionally uses zero mandatory approvals and no mandatory CODEOWNERS approval because all CODEOWNERS paths resolve to the PR author. This prevents an unsatisfiable self-review requirement while retaining deterministic review and promotion controls.

## Publication prerequisites

Before publication, independently verify all of the following against the exact final canonical source commit:

1. `Registry Validation` is green.
2. Candidate construction succeeds from the exact canonical source state.
3. Candidate hashes equal the reviewed values recorded for that exact source state.
4. `registry-v0.1.0` does not already exist as a tag or release.
5. Release sequence `1` does not collide with an existing trusted distribution.
6. The GitHub Release is created in `Baelfyre/Orchestra-Compliance-Registry` as non-draft and non-prerelease.
7. The release is made immutable before Orchestra network synchronization treats it as trusted provenance.
8. The ZIP, `release-manifest.json`, `release-manifest.sha256`, and ZIP SHA-256 evidence are published as independently reviewable release assets/evidence.
9. Orchestra end-to-end network sync validates the immutable canonical release boundary, exact release tag, manifest identity, bundle inventory, hashes, freshness, query, pinning, and anti-rollback behavior.
10. Orchestra v1.4.0 release readiness is refreshed after real Registry provenance evidence exists.

## Publication boundary

Candidate readiness and successful CI are evidence, not publication authority.

The following remain separate protected transitions:

- creating/publishing `registry-v0.1.0`;
- making the GitHub Release immutable;
- Orchestra public `v1.4.0` release/tag publication;
- marketplace/package publication;
- policy activation;
- deployment or production mutation;
- installed-integration refresh;
- destructive cleanup;
- branch deletion;
- force push or history rewrite.

## Verdict

`REGISTRY_V0_1_0_CANDIDATE_READY_FOR_EXPLICIT_PUBLICATION_GATE`
