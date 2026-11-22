import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from build_builtins import package
from theme_market import add, check, inspect, stage, static_path, PRIMARY, BACKUP


class ThemeMarketTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="maplesu-market-test-")
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.root = self.work / "catalog"
        self.root.mkdir()
        self.fpt = self.work / "fixture.fpt"
        self.preview = self.work / "cover.png"
        Image.new("RGB", (16, 16), "green").save(self.preview)
        package(dict(meta_name="Fixture", meta_version="1", meta_author="Tests"), {}, self.fpt)

    def add_fixture(self):
        add(self.root, "fixture", self.fpt, self.preview, "generated test fixture", "GPL-3.0")

    def test_add_retains_a_stable_id_metadata_and_provenance(self):
        self.add_fixture()
        entries = check(self.root)
        self.assertEqual(entries[0]["id"], "fixture")
        self.assertEqual(entries[0]["name"], "Fixture")
        self.assertTrue(list((self.root / "provenance").rglob("*.json")))

    def test_new_version_keeps_older_content_without_duplicate_catalog_ids(self):
        self.add_fixture()
        previous = check(self.root)[0]["download_url"]
        package(dict(meta_name="Fixture", meta_version="2"), {}, self.fpt)
        self.add_fixture()
        entries = check(self.root)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["version"], "2")
        self.assertTrue(static_path(self.root, previous).is_file())

    def test_same_version_different_bytes_are_rejected_without_partial_changes(self):
        self.add_fixture()
        before = (self.root / "index.json").read_bytes()
        package(dict(meta_name="Changed", meta_version="1"), {}, self.fpt)
        with self.assertRaisesRegex(ValueError, "increment meta_version"):
            self.add_fixture()
        self.assertEqual(before, (self.root / "index.json").read_bytes())
        self.assertEqual(1, len(list((self.root / "packages").rglob("*.fpt"))))

    def test_historical_versions_remain_immutable_after_a_new_release(self):
        self.add_fixture()
        package(dict(meta_name="Fixture", meta_version="2"), {}, self.fpt)
        self.add_fixture()
        package(dict(meta_name="Changed old release", meta_version="1"), {}, self.fpt)
        with self.assertRaises(ValueError):
            self.add_fixture()
        self.assertEqual("2", check(self.root)[0]["version"])

    def test_check_detects_mutated_packages(self):
        self.add_fixture()
        target = static_path(self.root, check(self.root)[0]["download_url"])
        package(dict(meta_name="Changed", meta_version="1"), {}, target)
        with self.assertRaises(ValueError):
            check(self.root)

    def test_stage_writes_absolute_fina_urls_and_never_overwrites_a_directory(self):
        self.add_fixture()
        output = self.work / "stage"
        stage(self.root, output, PRIMARY, BACKUP)
        entry = json.loads((output / "index.json").read_text(encoding="utf-8"))[0]
        self.assertTrue(entry["download_url"].startswith(PRIMARY))
        self.assertTrue(entry["download_mirrors"][0].startswith(BACKUP))
        self.assertFalse(json.loads((output / "catalog.json").read_text())["published"])
        self.assertTrue((output / ".nojekyll").is_file())
        with self.assertRaises(ValueError):
            stage(self.root, output, PRIMARY, BACKUP)

    def test_static_paths_never_leave_the_catalog(self):
        for value in ("../outside", "%2e%2e/outside", "https://example.org/file", "C:\\outside", "/outside"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                static_path(self.root, value)

    def test_inspect_rejects_resource_traversal_and_truncated_containers(self):
        package(dict(meta_name="Fixture"), {"../resource.png": b"fixture"}, self.fpt)
        with self.assertRaises(ValueError):
            inspect(self.fpt)
        self.fpt.write_bytes(self.fpt.read_bytes()[:-1])
        with self.assertRaises(ValueError):
            inspect(self.fpt)


if __name__ == "__main__":
    unittest.main()
