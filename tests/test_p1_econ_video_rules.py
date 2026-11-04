"""Economy video learning (4 Nov 2026): the rules learned from 37 reference videos enter the rulebook as 'proposed'.

They reach a section only after Navin locks them (rulebook governance); until then no prompt changes. The test checks
the file loads in the rulebook, names only sections BIE has, keeps ids unique, and that proposed rules stay out of the
makers' instructions.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import rulebook  # noqa: E402

PATH = ROOT / "bie" / "brain" / "rulebook" / "econ_videos.json"
SECTIONS = {"understand", "lesson", "showplan", "voice", "game", "notes", "review"}


class EconVideoRules(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(PATH.read_text(encoding="utf-8"))
        self.book = rulebook.load()

    def test_the_file_loads_with_unique_ids_and_known_sections(self):
        ids = [r["id"] for r in self.data["rules"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.startswith("EV-") for i in ids))
        for r in self.data["rules"]:
            self.assertTrue(set(r["sections"]) <= SECTIONS, r["id"])
            self.assertIn(r["status"], rulebook.STATUSES)
        self.assertIn("econ_videos@" + self.data["version"], self.book.version)

    def test_only_locked_rules_reach_a_maker(self):
        status = {r["id"]: r["status"] for r in self.data["rules"]}
        for section in SECTIONS:
            given = self.book.instructions(section)
            for rid, st in status.items():
                if st != "locked":
                    self.assertNotIn(f"[{rid}]", given, f"{rid} is {st} but reached {section}")


if __name__ == "__main__":
    unittest.main()
