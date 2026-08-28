from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import build_release, r7_query_gateway, r7_trusted_release

ROOT = Path(__file__).resolve().parents[1]


class R7TrustedReleaseTests(unittest.TestCase):
    def _build(self, temp: Path) -> Path:
        assets = temp / "assets"
        build_release.build_release(
            ROOT,
            assets,
            registry_version="0.4.0-test",
            release_sequence=4,
            release_tag="registry-v0.4.0-test",
        )
        return assets

    def test_verify_install_build_index_and_query(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            temp = Path(name)
            assets = self._build(temp)
            verified = r7_trusted_release.verify_release_assets(assets)
            self.assertEqual("0.4.0-test", verified.registry_version)
            self.assertEqual(4, verified.release_sequence)
            self.assertEqual("registry-v0.4.0-test", verified.release_tag)
            installed = temp / "installed"
            installed_verified, root = r7_trusted_release.install_release(assets, installed)
            self.assertEqual(verified.release_manifest_sha256, installed_verified.release_manifest_sha256)
            self.assertEqual(installed, root)
            index = temp / "r7.sqlite3"
            evidence = r7_trusted_release.build_verified_index(root, index, verified.release_manifest_sha256)
            self.assertTrue(evidence["canonical_json_remains_authority"])
            self.assertTrue(evidence["cache_rebuildable"])
            self.assertFalse(evidence["authority_expansion"])
            gateway = r7_query_gateway.RegistryQueryGateway(root, index, installed_verified.identity)
            result = gateway.query(r7_query_gateway.QuerySpec("obligations", domain="privacy", projection="EVIDENCE"))
            self.assertEqual("DIRECT_LOCAL_INDEXED_GATEWAY", result["backend"])
            self.assertEqual("TRUSTED_RELEASE_IDENTITY_VERIFIED", result["receipt"]["publication_trust"])
            self.assertFalse(result["receipt"]["authority_expansion"])

    def test_tampered_checksum_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            temp = Path(name)
            assets = self._build(temp)
            sidecar = assets / "orchestra-compliance-registry.zip.sha256"
            sidecar.write_text("0" * 64 + "  orchestra-compliance-registry.zip\n", encoding="utf-8")
            with self.assertRaises(r7_trusted_release.TrustedReleaseError):
                r7_trusted_release.verify_release_assets(assets)

    def test_existing_install_requires_explicit_replace(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            temp = Path(name)
            assets = self._build(temp)
            installed = temp / "installed"
            r7_trusted_release.install_release(assets, installed)
            with self.assertRaises(r7_trusted_release.TrustedReleaseError):
                r7_trusted_release.install_release(assets, installed)
            verified, root = r7_trusted_release.install_release(assets, installed, replace=True)
            self.assertEqual(installed, root)
            self.assertEqual("0.4.0-test", verified.registry_version)

    def test_installed_manifest_digest_binding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            temp = Path(name)
            assets = self._build(temp)
            installed = temp / "installed"
            verified, _ = r7_trusted_release.install_release(assets, installed)
            with self.assertRaises(r7_trusted_release.TrustedReleaseError):
                r7_trusted_release.load_installed_identity(installed, "0" * 64)
            loaded = r7_trusted_release.load_installed_identity(installed, verified.release_manifest_sha256)
            self.assertEqual(verified.release_manifest_sha256, loaded.release_manifest_sha256)


if __name__ == "__main__":
    unittest.main()
