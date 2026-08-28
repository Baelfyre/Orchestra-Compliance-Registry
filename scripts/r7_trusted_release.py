#!/usr/bin/env python3
"""Verify and install immutable Registry release assets for R7 consumers.

This module never creates trusted state. It only verifies a release bundle that was
already produced by ``scripts/build_release.py`` and supplied with its checksum
sidecars. The extracted canonical JSON remains authoritative; the SQLite index is a
derived disposable cache and may be rebuilt at any time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from scripts import r7_query_gateway, validate_registry
except ImportError:
    import r7_query_gateway  # type: ignore
    import validate_registry  # type: ignore

ASSET_NAME = "orchestra-compliance-registry.zip"
MANIFEST_NAME = "release-manifest.json"
CANONICAL_REPOSITORY = r7_query_gateway.REPOSITORY


class TrustedReleaseError(ValueError):
    pass


@dataclass(frozen=True)
class VerifiedRelease:
    registry_version: str
    release_sequence: int
    release_tag: str
    release_manifest_sha256: str
    bundle_sha256: str
    file_count: int

    @property
    def identity(self) -> r7_query_gateway.ReleaseIdentity:
        return r7_query_gateway.ReleaseIdentity(
            self.registry_version,
            self.release_tag,
            self.release_sequence,
            self.release_manifest_sha256,
        )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_sidecar(path: Path, expected_name: str) -> str:
    if not path.is_file():
        raise TrustedReleaseError(f"missing checksum sidecar: {path.name}")
    parts = path.read_text(encoding="utf-8").strip().split()
    if len(parts) != 2 or parts[1] != expected_name:
        raise TrustedReleaseError(f"invalid checksum sidecar: {path.name}")
    value = parts[0].lower()
    if r7_query_gateway.SHA256_RE.fullmatch(value) is None:
        raise TrustedReleaseError(f"invalid SHA-256 in {path.name}")
    return value


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrustedReleaseError(f"cannot read release manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise TrustedReleaseError("release manifest must be an object")
    return value


def _validate_manifest(value: dict[str, Any]) -> tuple[str, int, str, dict[str, str]]:
    if value.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise TrustedReleaseError("release canonical_repository mismatch")
    if value.get("status") != "TRUSTED_RELEASE":
        raise TrustedReleaseError("release manifest is not TRUSTED_RELEASE")
    version = value.get("registry_version")
    sequence = value.get("release_sequence")
    tag = value.get("release_tag")
    files = value.get("files")
    if not isinstance(version, str) or not version:
        raise TrustedReleaseError("release registry_version is invalid")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= 0:
        raise TrustedReleaseError("release_sequence must be a positive integer")
    if tag != f"registry-v{version}":
        raise TrustedReleaseError("release tag/version mismatch")
    if not isinstance(files, dict) or not files:
        raise TrustedReleaseError("release files map is missing")
    normalized: dict[str, str] = {}
    for relative, file_sha in files.items():
        if not isinstance(relative, str) or not relative.startswith("registry/"):
            raise TrustedReleaseError("release manifest contains unsafe file path")
        if ".." in Path(relative).parts or Path(relative).is_absolute():
            raise TrustedReleaseError("release manifest contains path traversal")
        if not isinstance(file_sha, str) or r7_query_gateway.SHA256_RE.fullmatch(file_sha) is None:
            raise TrustedReleaseError(f"invalid file digest for {relative}")
        normalized[relative] = file_sha
    return version, sequence, tag, normalized


def verify_release_assets(asset_dir: Path) -> VerifiedRelease:
    asset_dir = asset_dir.resolve()
    bundle = asset_dir / ASSET_NAME
    manifest_path = asset_dir / MANIFEST_NAME
    if not bundle.is_file() or not manifest_path.is_file():
        raise TrustedReleaseError("trusted release asset set is incomplete")
    expected_bundle_sha = _read_sidecar(asset_dir / f"{ASSET_NAME}.sha256", ASSET_NAME)
    expected_manifest_sha = _read_sidecar(asset_dir / "release-manifest.sha256", MANIFEST_NAME)
    actual_bundle_sha = _sha256_file(bundle)
    actual_manifest_sha = _sha256_file(manifest_path)
    if actual_bundle_sha != expected_bundle_sha:
        raise TrustedReleaseError("release bundle digest mismatch")
    if actual_manifest_sha != expected_manifest_sha:
        raise TrustedReleaseError("release manifest digest mismatch")
    manifest = _load_manifest(manifest_path)
    version, sequence, tag, files = _validate_manifest(manifest)
    with zipfile.ZipFile(bundle, "r") as archive:
        names = archive.namelist()
        expected_names = {MANIFEST_NAME, *files}
        if len(names) != len(set(names)) or set(names) != expected_names:
            raise TrustedReleaseError("release bundle member set mismatch")
        for name in names:
            path = Path(name)
            if path.is_absolute() or ".." in path.parts:
                raise TrustedReleaseError("release bundle contains unsafe path")
        embedded = archive.read(MANIFEST_NAME)
        if hashlib.sha256(embedded).hexdigest() != expected_manifest_sha:
            raise TrustedReleaseError("embedded release manifest digest mismatch")
        if json.loads(embedded) != manifest:
            raise TrustedReleaseError("embedded/external release manifest mismatch")
        for relative, expected in files.items():
            if hashlib.sha256(archive.read(relative)).hexdigest() != expected:
                raise TrustedReleaseError(f"release member digest mismatch: {relative}")
    return VerifiedRelease(version, sequence, tag, expected_manifest_sha, expected_bundle_sha, len(files))


def install_release(asset_dir: Path, install_dir: Path, *, replace: bool = False) -> tuple[VerifiedRelease, Path]:
    verified = verify_release_assets(asset_dir)
    asset_dir = asset_dir.resolve()
    install_dir = install_dir.resolve()
    if install_dir.exists():
        if not replace:
            raise TrustedReleaseError("install directory already exists; replacement requires explicit --replace")
        if install_dir.is_symlink() or not install_dir.is_dir():
            raise TrustedReleaseError("refusing to replace non-directory install target")
    parent = install_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="registry-r7-install-", dir=parent) as temp_name:
        staged = Path(temp_name) / "release"
        staged.mkdir()
        with zipfile.ZipFile(asset_dir / ASSET_NAME, "r") as archive:
            archive.extractall(staged)
        errors = validate_registry.validate(staged)
        if errors:
            raise TrustedReleaseError("installed trusted release failed Registry validation: " + "; ".join(errors))
        embedded_manifest_sha = _sha256_file(staged / MANIFEST_NAME)
        if embedded_manifest_sha != verified.release_manifest_sha256:
            raise TrustedReleaseError("installed release manifest identity drift")
        manifest = _load_manifest(staged / MANIFEST_NAME)
        registry_manifest = _load_manifest(staged / "registry" / "manifest.json")
        if registry_manifest.get("status") != "TRUSTED_RELEASE":
            raise TrustedReleaseError("installed Registry manifest is not TRUSTED_RELEASE")
        if registry_manifest.get("registry_version") != verified.registry_version:
            raise TrustedReleaseError("installed Registry version mismatch")
        if registry_manifest.get("release_sequence") != verified.release_sequence:
            raise TrustedReleaseError("installed Registry release sequence mismatch")
        if registry_manifest.get("release_tag") != verified.release_tag:
            raise TrustedReleaseError("installed Registry release tag mismatch")
        if manifest.get("canonical_repository") != registry_manifest.get("canonical_repository"):
            raise TrustedReleaseError("installed release/Registry repository identity mismatch")
        backup = None
        if install_dir.exists():
            backup = parent / f".{install_dir.name}.r7-replaced"
            if backup.exists():
                shutil.rmtree(backup)
            install_dir.rename(backup)
        try:
            shutil.copytree(staged, install_dir)
        except Exception:
            if backup is not None and not install_dir.exists():
                backup.rename(install_dir)
            raise
        if backup is not None:
            shutil.rmtree(backup)
    return verified, install_dir


def load_installed_identity(installed_root: Path, expected_manifest_sha256: str | None = None) -> VerifiedRelease:
    installed_root = installed_root.resolve()
    release_manifest = installed_root / MANIFEST_NAME
    registry_manifest_path = installed_root / "registry" / "manifest.json"
    if not release_manifest.is_file() or not registry_manifest_path.is_file():
        raise TrustedReleaseError("installed trusted release is incomplete")
    manifest_sha = _sha256_file(release_manifest)
    if expected_manifest_sha256 is not None and manifest_sha != expected_manifest_sha256:
        raise TrustedReleaseError("installed release manifest digest does not match expected identity")
    manifest = _load_manifest(release_manifest)
    version, sequence, tag, files = _validate_manifest(manifest)
    for relative, expected in files.items():
        path = installed_root / relative
        if not path.is_file() or _sha256_file(path) != expected:
            raise TrustedReleaseError(f"installed trusted file digest mismatch: {relative}")
    registry_manifest = _load_manifest(registry_manifest_path)
    if registry_manifest.get("status") != "TRUSTED_RELEASE":
        raise TrustedReleaseError("installed Registry manifest is not trusted")
    bundle_sha = "NOT_AVAILABLE_FROM_INSTALLED_TREE"
    return VerifiedRelease(version, sequence, tag, manifest_sha, bundle_sha, len(files))


def build_verified_index(installed_root: Path, index_path: Path, expected_manifest_sha256: str | None = None) -> dict[str, Any]:
    verified = load_installed_identity(installed_root, expected_manifest_sha256)
    meta = r7_query_gateway.build_index(index_path.resolve(), verified.identity, installed_root.resolve())
    return {
        "schema_version": "orchestra.compliance-registry.r7-trusted-cache-evidence.v1",
        "authority": "DERIVED_NON_AUTHORIZING",
        "registry_version": verified.registry_version,
        "release_sequence": verified.release_sequence,
        "release_tag": verified.release_tag,
        "release_manifest_sha256": verified.release_manifest_sha256,
        "installed_root": str(installed_root.resolve()),
        "index_path": str(index_path.resolve()),
        "index_meta": meta,
        "canonical_json_remains_authority": True,
        "cache_rebuildable": True,
        "authority_expansion": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify/install an immutable Registry release and optionally build an R7 cache")
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--install-dir", type=Path)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    try:
        verified = verify_release_assets(args.assets)
        result: dict[str, Any] = {"verified_release": asdict(verified), "authority_expansion": False}
        root: Path | None = None
        if args.install_dir is not None:
            verified, root = install_release(args.assets, args.install_dir, replace=args.replace)
            result["verified_release"] = asdict(verified)
            result["installed_root"] = str(root)
        if args.index is not None:
            if root is None:
                raise TrustedReleaseError("--index requires --install-dir")
            result["cache"] = build_verified_index(root, args.index, verified.release_manifest_sha256)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (TrustedReleaseError, r7_query_gateway.R7Error, OSError, zipfile.BadZipFile) as exc:
        print(f"R7_TRUSTED_RELEASE_FAIL={exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
