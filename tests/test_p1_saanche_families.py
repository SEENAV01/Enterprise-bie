"""Families of saanche (Sloman book, 5 November 2026): a family ships its own manifest in saanche.d/ beside its own
families/<name>.mjs, and the library takes it in; a name defined twice is refused."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bie.brain import formats, saanche

FAMILY = {"schema": "bie.saancha-manifest/1", "licence": "MIT (BIE)", "provenance": "test",
          "saanche": {"testFamilyThing": {"anchor": "center", "what": "a test drawing", "tags": ["test"],
                                          "params": {"w": {"type": "number", "default": 100, "min": 10, "max": 900}},
                                          "since": "2026-11-05"}}}


class Families(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copy(saanche.MANIFEST_PATH, self.tmp / "saanche.json")
        (self.tmp / "saanche.d").mkdir()
        self.patch = mock.patch.multiple(saanche, MANIFEST_PATH=self.tmp / "saanche.json", FAMILIES_DIR=self.tmp / "saanche.d")
        self.patch.start()
        saanche.manifest.cache_clear()

    def tearDown(self):
        self.patch.stop()
        saanche.manifest.cache_clear()
        shutil.rmtree(self.tmp)

    def test_a_family_joins_the_library(self):
        (self.tmp / "saanche.d" / "test.json").write_text(json.dumps(FAMILY), encoding="utf-8")
        names = saanche.names(saanche.MANIFEST_PATH)
        self.assertIn("testFamilyThing", names)
        self.assertIn("graph", names)
        self.assertEqual(saanche.problems("testFamilyThing", {"w": 50}, saanche.MANIFEST_PATH), [])
        self.assertTrue(saanche.problems("testFamilyThing", {"w": 5000}, saanche.MANIFEST_PATH))

    def test_a_name_defined_twice_is_refused(self):
        twice = dict(FAMILY, saanche={"graph": FAMILY["saanche"]["testFamilyThing"]})
        (self.tmp / "saanche.d" / "twice.json").write_text(json.dumps(twice), encoding="utf-8")
        with self.assertRaises(formats.FormatError):
            saanche.manifest(saanche.MANIFEST_PATH)

    def test_the_real_library_reads(self):
        self.patch.stop()
        saanche.manifest.cache_clear()
        self.assertIn("graph", saanche.names())
        self.patch.start()


if __name__ == "__main__":
    unittest.main()
