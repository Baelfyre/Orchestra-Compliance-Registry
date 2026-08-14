from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

try:
    from scripts import validate_registry
except ImportError:  # direct script execution
    import validate_registry  # type: ignore

CANONICAL_REPOSITORY = "Baelfyre/Orchestra-Compliance-Registry"
ASSET_NAME = "orchestra-compliance-registry.zip"
RELEASE_MANIFEST_NAME = "release-manifest.json"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class ReleaseBuildError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseBuildError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseBuildError(f"expected JSON object in {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_release_identity(registry_version: str, release_sequence: int, release_tag: str) -> None:
    if validate_registry.VERSION_TOKEN_RE.fullmatch(registry_version) is None:
        raise ReleaseBuildError("registry_version must be a safe version token")
    if not isinstance(release_sequence, int) or isinstance(release_sequence, bool) or release_sequence <= 0:
        raise ReleaseBuildError("release_sequence must be a positive integer")
    expected_tag = f"registry-v{registry_version}"
    if release_tag != expected_tag:
        raise ReleaseBuildError(f"release_tag must be {expected_tag}")


def _stage_registry(
    source_root: Path,
    stage_root: Path,
    *,
    registry_version: str,
    release_sequence: int,
    release_tag: str,
) -> None:
    source_manifest = _load_json(source_root / "registry" / "manifest.json")
    if source_manifest.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise ReleaseBuildError("source registry canonical_repository mismatch")
    if source_manifest.get("status") != "DRAFT" or source_manifest.get("release_sequence") != 0:
        raise ReleaseBuildError("release builder requires canonical DRAFT source state with release_sequence 0")

    shutil.copytree(source_root / "registry", stage_root / "registry")
    staged_manifest_path = stage_root / "registry" / "manifest.json"
    staged_manifest = _load_json(staged_manifest_path)
    staged_manifest["registry_version"] = registry_version
    staged_manifest["release_sequence"] = release_sequence
    staged_manifest["status"] = "TRUSTED_RELEASE"
    staged_manifest["release_tag"] = release_tag
    _write_json(staged_manifest_path, staged_manifest)

    errors = validate_registry.validate(stage_root)
    if errors:
        raise ReleaseBuildError("staged trusted registry failed semantic validation: " + "; ".join(errors))


def _release_files(stage_root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted((stage_root / "registry").rglob("*")):
        if path.is_file():
            relative = path.relative_to(stage_root).as_posix()
            files[relative] = _sha256_file(path)
    if not files:
        raise ReleaseBuildError("release contains no registry files")
    return files


def _write_deterministic_zip(stage_root: Path, release_files: dict[str, str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    members = [RELEASE_MANIFEST_NAME, *sorted(release_files)]
    with zipfile.ZipFile(output_path, "w") as archive:
        for relative in members:
            data = (stage_root / relative).read_bytes()
            info = zipfile.ZipInfo(relative, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_release(
    source_root: Path,
    output_dir: Path,
    *,
    registry_version: str,
    release_sequence: int,
    release_tag: str,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    output_dir = output_dir.resolve()
    _validate_release_identity(registry_version, release_sequence, release_tag)

    source_errors = validate_registry.validate(source_root)
    if source_errors:
        raise ReleaseBuildError("source registry failed semantic validation: " + "; ".join(source_errors))

    with tempfile.TemporaryDirectory(prefix="registry-release-") as temp_dir:
        stage_root = Path(temp_dir)
        _stage_registry(
            source_root,
            stage_root,
            registry_version=registry_version,
            release_sequence=release_sequence,
            release_tag=release_tag,
        )
        release_files = _release_files(stage_root)
        release_manifest = {
            "schema_version": 1,
            "canonical_repository": CANONICAL_REPOSITORY,
            "registry_version": registry_version,
            "release_sequence": release_sequence,
            "release_tag": release_tag,
            "status": "TRUSTED_RELEASE",
            "files": release_files,
        }
        manifest_path = stage_root / RELEASE_MANIFEST_NAME
        _write_json(manifest_path, release_manifest)
        manifest_sha256 = _sha256_file(manifest_path)

        output_dir.mkdir(parents=True, exist_ok=True)
        external_manifest = output_dir / RELEASE_MANIFEST_NAME
        shutil.copy2(manifest_path, external_manifest)
        (output_dir / "release-manifest.sha256").write_text(
            f"{manifest_sha256}  {RELEASE_MANIFEST_NAME}\n", encoding="utf-8"
        )

        asset_path = output_dir / ASSET_NAME
        _write_deterministic_zip(stage_root, release_files, asset_path)
        asset_sha256 = _sha256_file(asset_path)
        (output_dir / f"{ASSET_NAME}.sha256").write_text(
            f"{asset_sha256}  {ASSET_NAME}\n", encoding="utf-8"
        )

    return {
        "registry_version": registry_version,
        "release_sequence": release_sequence,
        "release_tag": release_tag,
        "manifest_sha256": manifest_sha256,
        "asset_sha256": asset_sha256,
        "asset": str(output_dir / ASSET_NAME),
        "manifest": str(output_dir / RELEASE_MANIFEST_NAME),
        "file_count": len(release_files),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--registry-version", required=True)
    parser.add_argument("--release-sequence", type=int, required=True)
    parser.add_argument("--release-tag", required=True)
    args = parser.parse_args()
    try:
        result = build_release(
            Path(args.root),
            Path(args.output_dir),
            registry_version=args.registry_version,
            release_sequence=args.release_sequence,
            release_tag=args.release_tag,
        )
    except ReleaseBuildError as exc:
        print(f"RELEASE_BUILD_FAIL={exc}")
        return 1
    print("RELEASE_BUILD_PASS=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
