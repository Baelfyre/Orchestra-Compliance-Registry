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
VERSION = "test-candidate"
SEQUENCE = 1
TAG = "registry-vtest-candidate"
PUBLISHED_V0_1_MANIFEST_SHA256 = "9922ddcce77dfac0c01cac80fe6669aaffe37636826a56a4b54a8312558ee2d1"
PUBLISHED_V0_1_ASSET_SHA256 = "b64889933d30a8dea27bcbbb95c952e4f053c14a4f345e1e04b27777b5025ec0"
PUBLISHED_V0_2_MANIFEST_SHA256 = "cb98e4496da8952cff1432207d57f04379364bac2e95cc422de173681a8fb2b4"
PUBLISHED_V0_2_ASSET_SHA256 = "71414aaead10634c2a4b79ec519b4fc76fb32af71cd831ef48f2133bcc211388"
PUBLISHED_V0_3_MANIFEST_SHA256 = "2674c7625188e20047274f3f3e7a25836299c640913bfc2eb20de2d4349808a9"
PUBLISHED_V0_3_ASSET_SHA256 = "dc74b59f3c11dd7c740a91a4c6667064b84c3505d8bfc62382cd2ce0f4f0bfea"
PUBLISHED_V0_4_MANIFEST_SHA256 = "040d6576cf10e9f7e3a9a051792869541c1d33b7af3c665fad8eecb939c7baaa"
PUBLISHED_V0_4_ASSET_SHA256 = "e0457a75837d169d7bb8a7da14d8f4141d35a691952ff8f8978ef793e3cf92d3"


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
            expected_file_count = sum(1 for path in (ROOT / "registry").rglob("*") if path.is_file())
            self.assertEqual(expected_file_count, result["file_count"])
            self.assertTrue(all(path.startswith("registry/") for path in manifest["files"]))
            self.assertFalse(any(path.startswith("machine/") for path in manifest["files"]))

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
                self.assertFalse(any(name.startswith("machine/") for name in names))
                bundled_manifest = json.loads(archive.read(build_release.RELEASE_MANIFEST_NAME))
                self.assertEqual(manifest, bundled_manifest)
                staged_registry_manifest = json.loads(archive.read("registry/manifest.json"))
                self.assertEqual("TRUSTED_RELEASE", staged_registry_manifest["status"])
                self.assertEqual(VERSION, staged_registry_manifest["registry_version"])
                self.assertEqual(SEQUENCE, staged_registry_manifest["release_sequence"])
                self.assertEqual(TAG, staged_registry_manifest["release_tag"])
                for relative, expected_digest in manifest["files"].items():
                    self.assertEqual(expected_digest, hashlib.sha256(archive.read(relative)).hexdigest())

    def test_published_v0_1_identity_remains_frozen_in_history(self) -> None:
        history = json.loads((ROOT / "machine" / "trusted-release-history.json").read_text(encoding="utf-8"))
        matches = [item for item in history["releases"] if item["tag"] == "registry-v0.1.0"]
        self.assertEqual(1, len(matches))
        trusted = matches[0]
        self.assertEqual("0.1.0", trusted["registry_version"])
        self.assertEqual(1, trusted["release_sequence"])
        self.assertEqual("3821bcb55125b4d8864f28b6423650e6e17ac67b", trusted["target_commit"])
        self.assertEqual(PUBLISHED_V0_1_MANIFEST_SHA256, trusted["release_manifest_sha256"])
        self.assertEqual(PUBLISHED_V0_1_ASSET_SHA256, trusted["bundle_sha256"])
        self.assertTrue(trusted["immutable"])
        self.assertFalse(trusted["draft"])
        self.assertFalse(trusted["prerelease"])

    def test_published_v0_2_identity_remains_frozen_in_history(self) -> None:
        history = json.loads((ROOT / "machine" / "trusted-release-history.json").read_text(encoding="utf-8"))
        matches = [item for item in history["releases"] if item["tag"] == "registry-v0.2.0"]
        self.assertEqual(1, len(matches))
        trusted = matches[0]
        self.assertEqual("0.2.0", trusted["registry_version"])
        self.assertEqual(2, trusted["release_sequence"])
        self.assertEqual("cb32038a2683eb2c19f52646892d3257996a06eb", trusted["target_commit"])
        self.assertEqual(PUBLISHED_V0_2_MANIFEST_SHA256, trusted["release_manifest_sha256"])
        self.assertEqual(PUBLISHED_V0_2_ASSET_SHA256, trusted["bundle_sha256"])
        self.assertTrue(trusted["immutable"])
        self.assertFalse(trusted["draft"])
        self.assertFalse(trusted["prerelease"])

    def test_published_v0_3_identity_remains_frozen_in_history(self) -> None:
        history = json.loads((ROOT / "machine" / "trusted-release-history.json").read_text(encoding="utf-8"))
        matches = [item for item in history["releases"] if item["tag"] == "registry-v0.3.0"]
        self.assertEqual(1, len(matches))
        trusted = matches[0]
        self.assertEqual("0.3.0", trusted["registry_version"])
        self.assertEqual(3, trusted["release_sequence"])
        self.assertEqual("20eb859db153f17e24c052a13765e982d51cedbf", trusted["target_commit"])
        self.assertEqual(PUBLISHED_V0_3_MANIFEST_SHA256, trusted["release_manifest_sha256"])
        self.assertEqual(PUBLISHED_V0_3_ASSET_SHA256, trusted["bundle_sha256"])
        self.assertTrue(trusted["immutable"])
        self.assertFalse(trusted["draft"])
        self.assertFalse(trusted["prerelease"])

    def test_current_trusted_release_is_v0_4_and_matches_history(self) -> None:
        publication = json.loads((ROOT / "machine" / "publication-state.json").read_text(encoding="utf-8"))
        history = json.loads((ROOT / "machine" / "trusted-release-history.json").read_text(encoding="utf-8"))
        trusted = publication["trusted_release"]
        self.assertEqual("registry-v0.4.0", trusted["tag"])
        self.assertEqual("registry-v0.4.0", history["current_trusted_release"])
        matches = [item for item in history["releases"] if item["tag"] == trusted["tag"]]
        self.assertEqual(1, len(matches))
        historical = matches[0]
        self.assertEqual("0.4.0", trusted["registry_version"])
        self.assertEqual(4, trusted["release_sequence"])
        self.assertEqual("488c979b37dd84d8645fd8e6c288d297375c4e5b", trusted["target_commit"])
        self.assertEqual(PUBLISHED_V0_4_MANIFEST_SHA256, trusted["release_manifest_sha256"])
        self.assertEqual(PUBLISHED_V0_4_ASSET_SHA256, trusted["bundle_sha256"])
        for key in (
            "release_id",
            "registry_version",
            "release_sequence",
            "target_commit",
            "draft",
            "prerelease",
            "immutable",
            "published_at",
            "release_manifest_sha256",
            "bundle_sha256",
            "required_assets",
        ):
            self.assertEqual(trusted[key], historical[key], key)

    def test_two_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = self.build(Path(first_dir))
            second = self.build(Path(second_dir))
            self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
            self.assertEqual(first["asset_sha256"], second["asset_sha256"])
            self.assertEqual(Path(first["asset"]).read_bytes(), Path(second["asset"]).read_bytes())
            self.assertEqual(Path(first["manifest"]).read_bytes(), Path(second["manifest"]).read_bytes())

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
                    release_tag="registry-vdifferent-candidate",
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
