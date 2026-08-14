from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts import build_release

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
SEQUENCE = 1
TAG = "registry-v0.1.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ReleaseBuilderTests(unittest.TestCase):
    def build(self, output_dir: Path, *, source_root: Path = ROOT) -> dict:
        return build_release.build_release(
            source_root,
            output_dir,
            registry_version=VERSION,
            release_sequence=SEQUENCE,
            release_tag=TAG,
        )

    def source_fixture(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(ROOT / "registry", root / "registry")
        return temp, root

    def test_release_bundle_contract_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            result = self.build(output)
            asset = Path(result["asset"])
            external_manifest = Path(result["manifest"])

            manifest_bytes = external_manifest.read_bytes()
            manifest = json.loads(manifest_bytes)
            self.assertEqual(1, manifest["schema_version"])
            self.assertEqual(build_release.CANONICAL_REPOSITORY, manifest["canonical_repository"])
            self.assertEqual(VERSION, manifest["registry_version"])
            self.assertEqual(SEQUENCE, manifest["release_sequence"])
            self.assertEqual(TAG, manifest["release_tag"])
            self.assertEqual("TRUSTED_RELEASE", manifest["status"])
            self.assertNotIn(build_release.RELEASE_MANIFEST_NAME, manifest["files"])

            manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
            self.assertEqual(manifest_digest, result["manifest_sha256"])
            self.assertEqual(
                f"{manifest_digest}  {build_release.RELEASE_MANIFEST_NAME}\n",
                (output / "release-manifest.sha256").read_text(encoding="utf-8"),
            )
            self.assertEqual(result["asset_sha256"], sha256(asset))
            self.assertEqual(
                f"{result['asset_sha256']}  {build_release.ASSET_NAME}\n",
                (output / f"{build_release.ASSET_NAME}.sha256").read_text(encoding="utf-8"),
            )

            with zipfile.ZipFile(asset) as archive:
                names = archive.namelist()
                self.assertEqual(
                    [build_release.RELEASE_MANIFEST_NAME, *sorted(manifest["files"])],
                    names,
                )
                bundled_manifest = json.loads(archive.read(build_release.RELEASE_MANIFEST_NAME))
                self.assertEqual(manifest, bundled_manifest)
                staged_registry_manifest = json.loads(archive.read("registry/manifest.json"))
                self.assertEqual("TRUSTED_RELEASE", staged_registry_manifest["status"])
                self.assertEqual(VERSION, staged_registry_manifest["registry_version"])
                self.assertEqual(SEQUENCE, staged_registry_manifest["release_sequence"])
                self.assertEqual(TAG, staged_registry_manifest["release_tag"])
                for relative, expected_digest in manifest["files"].items():
                    self.assertEqual(expected_digest, hashlib.sha256(archive.read(relative)).hexdigest())

    def test_two_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = self.build(Path(first_dir))
            second = self.build(Path(second_dir))
            self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
            self.assertEqual(first["asset_sha256"], second["asset_sha256"])
            self.assertEqual(
                Path(first["asset"]).read_bytes(),
                Path(second["asset"]).read_bytes(),
            )
            self.assertEqual(
                Path(first["manifest"]).read_bytes(),
                Path(second["manifest"]).read_bytes(),
            )

    def test_zero_release_sequence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(build_release.ReleaseBuildError, "positive integer"):
                build_release.build_release(
                    ROOT,
                    Path(temp_dir),
                    registry_version=VERSION,
                    release_sequence=0,
                    release_tag=TAG,
                )

    def test_mismatched_release_tag_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(build_release.ReleaseBuildError, "release_tag must be"):
                build_release.build_release(
                    ROOT,
                    Path(temp_dir),
                    registry_version=VERSION,
                    release_sequence=SEQUENCE,
                    release_tag="registry-v0.1.1",
                )

    def test_invalid_source_registry_blocks_packaging(self) -> None:
        temp, root = self.source_fixture()
        try:
            status_path = root / "registry" / "source-status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["entries"] = status["entries"][:-1]
            status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
            with tempfile.TemporaryDirectory() as output_dir:
                with self.assertRaisesRegex(build_release.ReleaseBuildError, "source registry failed semantic validation"):
                    self.build(Path(output_dir), source_root=root)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
