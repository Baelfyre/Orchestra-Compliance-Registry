# Registry Governance

## Purpose

This repository publishes reusable compliance intelligence for Orchestra. It does not publish legal advice or project-specific compliance approvals.

## Authority model

- Public users may read, fork, and propose changes.
- Only explicitly authorized maintainers may approve canonical changes.
- Direct changes to protected canonical branches are not part of the trusted workflow.
- Source-monitor automation may discover changes and open or update proposals, but it must not approve, merge, or publish trusted registry releases.
- Registry content never grants Orchestra execution, deployment, release, destructive-operation, risk-acceptance, or policy-activation authority.

## Canonical change path

1. A change is proposed on a non-canonical branch or pull request.
2. Validation runs without repository secrets on untrusted contribution content.
3. Source identity, authority, currentness, applicability metadata, and supersession are reviewed.
4. Required human review is completed for interpretation or policy choices.
5. Canonical state is updated only through the protected review path.
6. A trusted registry release is a separate action after canonical validation.

## Required repository controls

The intended GitHub controls for `main` are:

- require pull requests before merge
- require at least one approving review by an authorized maintainer
- require CODEOWNERS review for protected paths
- dismiss stale approvals when the proposed change changes
- require the registry validation status check
- require conversation resolution
- block force pushes
- block branch deletion
- minimize bypass permissions

Repository settings are enforcement state and must be verified independently. This file describes the intended policy and does not prove that GitHub settings are active.

## Legal and licensing decisions

The repository data-license choice remains a separate human governance decision. No contributor or automation may infer a license grant that has not been explicitly published.
