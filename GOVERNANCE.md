# Registry Governance

## Purpose

This repository publishes reusable compliance intelligence for Orchestra. It does not publish legal advice or project-specific compliance approvals.

## Authority model

- Public users may read, fork, and propose changes.
- Only explicitly authorized maintainers may approve canonical changes.
- Direct changes to protected canonical branches are not part of the trusted workflow.
- Source-monitor automation may discover changes and open or update proposals, but it must not approve, merge, or publish trusted registry releases.
- Registry content never grants Orchestra execution, deployment, release, destructive-operation, risk-acceptance, or policy-activation authority.

## Machine and human representation

Repository machine state is JSON-first. `registry/manifest.json`, the Registry records it references, and machine records under `machine/` are the structured inputs for tooling and agent consumption.

Markdown files are human-readable governance, explanation, rationale, and historical evidence. Where a corresponding machine record exists, Markdown must not override it and tooling must not reconstruct machine state by parsing prose.

`machine/representation-policy.json` defines this representation boundary. `machine/publication-state.json` records the last verified source/publication identity, while the live immutable GitHub Release remains external publication reality and must be independently re-read before trust or mutation.

Machine metadata under `machine/` is not distributed Registry content. The trusted release builder packages `registry/`; moving control metadata into that root would change release bytes and requires a separately governed distribution-version decision.

## Canonical change path

1. A change is proposed on a non-canonical branch or pull request.
2. Validation runs without repository secrets on untrusted contribution content.
3. Source identity, authority, currentness, applicability metadata, and supersession are reviewed.
4. Required human review is completed for interpretation or policy choices.
5. Canonical state is updated only through the protected review path.
6. A trusted registry release is a separate action after canonical validation.

The foundation bootstrap does not waive these controls. Before the first registry-foundation pull request is merged, the required `main` repository controls below must be independently verified as active. Missing protection or required checks is a governance `HOLD`, not permission to merge through an unprotected branch.

## Required repository controls

The intended GitHub controls for `main` are:

- require pull requests before merge
- require at least one approving review by an authorized maintainer
- require CODEOWNERS review for protected paths
- dismiss stale approvals when the proposed change changes
- require the `Registry Validation` status check
- require conversation resolution
- block force pushes
- block branch deletion
- minimize bypass permissions

Repository settings are enforcement state and must be verified independently. This file describes the intended policy and does not prove that GitHub settings are active.

## Trusted registry release boundary

A canonical merge is not automatically a trusted registry release. Trusted release publication remains a separate protected action.

A trusted registry release must:

- be produced from canonical validated registry state;
- use a positive monotonic `release_sequence`;
- use a release manifest that identifies `Baelfyre/Orchestra-Compliance-Registry`, the registry version, release tag, and exact SHA-256 for every distributed registry file;
- contain no unlisted distributed files;
- publish the release-manifest SHA-256 as independently readable release evidence for offline/pre-downloaded verification;
- be a non-draft, non-prerelease, immutable GitHub Release in the canonical repository before normal network synchronization may trust it.

A self-consistent archive does not establish provenance by itself. Orchestra network synchronization trusts the immutable canonical GitHub Release boundary plus the verified manifest. Offline/local installation requires the separately obtained expected release-manifest SHA-256 as its out-of-band trust anchor.

## Legal and licensing decisions

The repository data-license choice remains a separate human governance decision. No contributor or automation may infer a license grant that has not been explicitly published.
