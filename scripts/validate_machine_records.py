from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

CANONICAL_REPOSITORY = "Baelfyre/Orchestra-Compliance-Registry"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
POLICY_PATH = "machine/representation-policy.json"
PUBLICATION_PATH = "machine/publication-state.json"
MANIFEST_PATH = "registry/manifest.json"
REQUIRED_RULES = {
    "MACHINE_JSON_PRECEDES_MARKDOWN",
    "MARKDOWN_MUST_NOT_OVERRIDE_MACHINE_STATE",
    "NO_MACHINE_STATE_RECONSTRUCTION_FROM_MARKDOWN_WHEN_JSON_EXISTS",
    "MACHINE_STATE_CHANGES_REQUIRE_MACHINE_RECORD_UPDATE_FIRST",
    "LIVE_EXTERNAL_REALITY_OVERRIDES_STALE_REPOSITORY_RECORD",
}
REQUIRED_ASSETS = {
    "orchestra-compliance-registry.zip",
    "orchestra-compliance-registry.zip.sha256",
    "release-manifest.json",
    "release-manifest.sha256",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def validate(root: Path) -> list[str]:
    try:
        policy = load_json(root / POLICY_PATH)
        publication = load_json(root / PUBLICATION_PATH)
        manifest = load_json(root / MANIFEST_PATH)

        if policy.get("schema_version") != "orchestra.compliance-registry.representation-policy.v1":
            raise ValueError("unexpected representation policy schema")
        if policy.get("canonical_repository") != CANONICAL_REPOSITORY:
            raise ValueError("representation policy canonical_repository mismatch")
        if policy.get("machine_priority") is not True:
            raise ValueError("machine_priority must remain true")
        if policy.get("markdown_role") != "NON_AUTHORITATIVE_HUMAN_READABLE_REFERENCE":
            raise ValueError("Markdown must remain non-authoritative human-readable reference")
        if policy.get("machine_state_must_not_depend_on_markdown_parsing") is not True:
            raise ValueError("machine state must not depend on Markdown parsing")

        machine_authority = policy.get("machine_authority")
        if not isinstance(machine_authority, dict):
            raise ValueError("machine_authority must be an object")
        if machine_authority.get("editable_registry_state") != MANIFEST_PATH:
            raise ValueError("editable Registry machine authority must be registry/manifest.json")
        if machine_authority.get("publication_state") != PUBLICATION_PATH:
            raise ValueError("publication machine authority must be machine/publication-state.json")
        if machine_authority.get("registry_records_from_manifest") is not True:
            raise ValueError("Registry record paths must be resolved from the machine manifest")
        for label, path in machine_authority.items():
            if isinstance(path, str) and path.lower().endswith(".md"):
                raise ValueError(f"Markdown cannot be machine authority: {label}={path}")

        bundle_boundary = policy.get("release_bundle_boundary")
        if not isinstance(bundle_boundary, dict):
            raise ValueError("release_bundle_boundary must be an object")
        if bundle_boundary.get("distributed_root") != "registry/":
            raise ValueError("distributed Registry root must remain registry/")
        if bundle_boundary.get("machine_metadata_root") != "machine/":
            raise ValueError("machine metadata root must remain machine/")
        if bundle_boundary.get("machine_metadata_is_distributed_registry_content") is not False:
            raise ValueError("machine metadata must not silently enter the trusted Registry distribution")

        human_views = policy.get("human_views")
        if not isinstance(human_views, dict) or not human_views:
            raise ValueError("human_views must be a non-empty object")
        if not all(isinstance(path, str) and path.endswith(".md") for path in human_views):
            raise ValueError("human views must point to Markdown paths")
        rules = policy.get("rules")
        if not isinstance(rules, list) or not REQUIRED_RULES.issubset(set(rules)):
            raise ValueError("representation policy is missing required JSON-first rules")

        external = policy.get("external_source_reality")
        if not isinstance(external, dict):
            raise ValueError("external_source_reality must be an object")
        if external.get("trusted_publication") != "immutable_github_release":
            raise ValueError("trusted publication source reality must remain immutable GitHub Release")
        if external.get("live_external_reality_overrides_stale_repository_record") is not True:
            raise ValueError("live external reality must override stale repository records")

        if publication.get("schema_version") != "orchestra.compliance-registry.publication-state.v1":
            raise ValueError("unexpected publication-state schema")
        if publication.get("canonical_repository") != CANONICAL_REPOSITORY:
            raise ValueError("publication-state canonical_repository mismatch")

        source = publication.get("editable_source")
        if not isinstance(source, dict):
            raise ValueError("editable_source must be an object")
        if source.get("manifest_path") != MANIFEST_PATH:
            raise ValueError("publication state must reference registry/manifest.json")
        for field in ("registry_version", "release_sequence", "status"):
            if source.get(field) != manifest.get(field):
                raise ValueError(f"publication editable_source {field} drifted from manifest")
        if source.get("status") != "DRAFT" or source.get("release_sequence") != 0:
            raise ValueError("canonical editable source must remain DRAFT release_sequence 0")

        boundary = publication.get("repository_source_boundary")
        if not isinstance(boundary, dict):
            raise ValueError("repository_source_boundary must be an object")
        if boundary.get("canonical_branch") != "main":
            raise ValueError("repository source boundary canonical_branch must be main")
        if not isinstance(boundary.get("observed_sha"), str) or SHA_RE.fullmatch(boundary["observed_sha"]) is None:
            raise ValueError("repository source boundary observed_sha must be a full lowercase Git SHA")
        if boundary.get("state_class") != "VERIFIED_REPOSITORY_CHECKPOINT":
            raise ValueError("repository source boundary state_class mismatch")
        if boundary.get("semantics") != "LAST_EXPLICITLY_VERIFIED_REPOSITORY_BOUNDARY_NOT_CURRENT_HEAD_CLAIM":
            raise ValueError("repository source boundary must not claim to be the current head")
        if boundary.get("live_head_reverification_required") is not True:
            raise ValueError("live repository head re-verification must remain required")
        if "repository_main" in publication:
            raise ValueError("publication state must not use self-invalidating repository_main current-head semantics")

        trusted = publication.get("trusted_release")
        if not isinstance(trusted, dict):
            raise ValueError("trusted_release must be an object")
        if trusted.get("state") != "PUBLISHED_IMMUTABLE_VERIFIED":
            raise ValueError("trusted release must be PUBLISHED_IMMUTABLE_VERIFIED")
        if trusted.get("draft") is not False or trusted.get("prerelease") is not False or trusted.get("immutable") is not True:
            raise ValueError("trusted release must be non-draft, non-prerelease, and immutable")
        if not isinstance(trusted.get("release_sequence"), int) or trusted["release_sequence"] <= source["release_sequence"]:
            raise ValueError("trusted release sequence must be greater than editable source sequence")
        if trusted.get("tag") != f"registry-v{trusted.get('registry_version')}":
            raise ValueError("trusted release tag/version mismatch")
        if not isinstance(trusted.get("target_commit"), str) or SHA_RE.fullmatch(trusted["target_commit"]) is None:
            raise ValueError("trusted release target_commit must be a full lowercase Git SHA")
        for field in ("release_manifest_sha256", "bundle_sha256"):
            value = trusted.get(field)
            if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
                raise ValueError(f"trusted release {field} must be lowercase SHA-256")
        assets = trusted.get("required_assets")
        if not isinstance(assets, list) or set(assets) != REQUIRED_ASSETS or len(assets) != len(REQUIRED_ASSETS):
            raise ValueError("trusted release required asset inventory mismatch")

        verification = publication.get("verification")
        if not isinstance(verification, dict):
            raise ValueError("verification must be an object")
        if verification.get("repository_source_boundary_verified") is not True:
            raise ValueError("repository source boundary must be explicitly verified")
        if verification.get("external_reverification_required_before_trust_or_mutation") is not True:
            raise ValueError("live external re-verification must remain required before trust or mutation")

        authority = publication.get("authority")
        if not isinstance(authority, dict):
            raise ValueError("authority must be an object")
        if authority.get("editable_source_authority") != MANIFEST_PATH:
            raise ValueError("editable source authority mismatch")
        if authority.get("repository_head_source_reality") != "LIVE_GITHUB_MAIN":
            raise ValueError("repository head source reality must remain live GitHub main")
        if authority.get("publication_source_reality") != "IMMUTABLE_GITHUB_RELEASE":
            raise ValueError("publication source reality must remain immutable GitHub Release")
        if authority.get("repository_checkpoint_semantics") != "LAST_VERIFIED_CHECKPOINT_NOT_CURRENT_HEAD_CLAIM":
            raise ValueError("repository checkpoint semantics mismatch")
        if authority.get("markdown_authority") is not False:
            raise ValueError("Markdown must not gain publication authority")

        companions = publication.get("human_companions")
        if not isinstance(companions, list) or not all(isinstance(path, str) and path.endswith(".md") for path in companions):
            raise ValueError("human companions must be Markdown references")

        return []
    except ValueError as exc:
        return [str(exc)]


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("REGISTRY_MACHINE_RECORDS_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
