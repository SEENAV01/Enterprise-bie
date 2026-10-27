"""Seekh from the Money chapter's first scripts (VM job t046c-money-lesson-b, 27 October 2026): 17 of 18 scripts failed, 11 of them
with nothing left but S2-04 flags on everyday words of money, shops, banks and payments that the everyday-Hindi list lacked (746 flags
over the rounds, रकम alone 104 times), and the Codex checker found 5 scripts pointing at BIE's own source packet ('supplied figure',
'source-listed', 'answer codes in the original continuation') instead of teaching. Now the list knows those words (formal ones stay
hard) and W-01 catches the source-pointing phrases in code. Every text below is test input, never lesson content.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import hinglish, rulebook, soul  # noqa: E402

BOOK = rulebook.load()
SIMPLE = hinglish.load()

EVERYDAY = ("रकम", "वादा", "भुगतान", "गेहूँ", "बकाया", "जेब", "बटुआ", "बोरी", "किराया", "सौदा", "रसीद", "पर्ची", "हथेली", "सुनार",
            "तराज़ू", "चायवाला", "दूधवाला", "साबुन", "जूते", "साइकिल", "मुफ्त", "खजाना", "तारीख", "चोरी", "टोकरी", "बेटी", "नकदी",
            "रिश्तेदार", "छुट्टे", "किलो", "लागत", "कौड़ियाँ", "सदी", "डाक", "चिट्ठी", "चम्मच", "घड़ी", "फोन", "बिल", "शून्य", "संकट",
            "विकल्प", "अनुमति", "सफल", "लिखित", "दर", "मुद्दा", "सिफारिश", "ब्रिटिश", "उन्होंने")
INFLECTED = ("वादे", "बकाये", "रुपये", "सुविधाएँ", "तारीखें", "जेबें", "बटुए", "बोरों", "सौदों", "खातों", "मंज़ूरी", "अड़चनें", "निभेंगे",
             "ठुकराया", "खबरें", "भुनाकर", "शिकायतों", "सीढ़ियाँ", "चायवाले", "बिकती", "अटकेंगे", "मालिकों", "कारोबारियों", "बंदिशें",
             "मवेशियों", "विकल्पों", "जँची", "फैलायी")
FORMAL = ("काल्पनिक", "कल्पित", "निर्देश", "मान्यता", "मुख्यतः", "महत्त्वपूर्ण", "दायित्व", "व्यापक", "संस्था", "अधिकतम", "अवधि", "परिभाषा",
          "प्रशासन", "निर्णायक", "पर्याप्त", "प्रतिनिधि", "सफलतापूर्वक", "अनिवार्य", "स्थापना")


class TheMoneyWords(unittest.TestCase):
    def test_everyday_words_of_money_shops_and_banks_are_simple(self):
        for word in EVERYDAY + INFLECTED:
            self.assertTrue(SIMPLE.is_simple(word), word)

    def test_formal_words_stay_hard(self):
        for word in FORMAL:
            self.assertFalse(SIMPLE.is_simple(word), word)

    def test_a_shop_sentence_passes_and_a_formal_one_is_flagged(self):
        self.assertEqual(hinglish.difficult_words("दुकानदार ने रकम गिनी और वादा किया कि बकाया कल देगा; रसीद जेब में रखो।"), [])
        self.assertEqual(hinglish.difficult_words("यह काल्पनिक उदाहरण मुख्यतः निर्देश के तहत है।"), ["काल्पनिक", "मुख्यतः", "निर्देश", "तहत"])

    def test_the_list_version_and_its_changes_line(self):
        self.assertIn("simple_hindi@2026-10-27.2", BOOK.version)
        import json
        data = json.loads((ROOT / "bie/brain/rulebook/simple_hindi.json").read_text(encoding="utf-8"))
        self.assertEqual(data["version"], "2026-10-27.2")
        self.assertTrue(data["changes"][0].startswith("2026-10-27.2"))
        self.assertIn("रकम", data["changes"][0])


class SourcePointing(unittest.TestCase):
    """W-01: a beat that points at BIE's own source packet is as useless to the learner as one that points at the book."""

    def beats(self, *says):
        return [{"beat_id": f"b{n}", "say": say} for n, say in enumerate(says, 1)]

    def test_the_checkers_findings_are_now_caught_by_code(self):
        problems = soul.wording_problems(self.beats("Supplied figure के हिसाब से RBI ने 1935 में notes छापे।",
                                                    "Source-listed numbers बाद में verify होंगे।",
                                                    "Answer codes original continuation में हैं।",
                                                    "The source text gives the date as October 2022."))
        self.assertEqual(len(problems), 4)
        self.assertTrue(all("(W-01)" in p for p in problems))

    def test_ordinary_teaching_with_the_word_source_is_not_flagged(self):
        self.assertEqual(soul.wording_problems(self.beats("Energy का source सूरज है।", "Resource allocation समझो: पैसा कहाँ जाए।",
                                                          "सही answer C है, क्योंकि MDR एक charge है।",
                                                          "RBI ने 1935 में पहले notes छापे; उन पर George V की तस्वीर थी।")), [])

    def test_the_grammar_version_moved_with_its_changes_line(self):
        self.assertIn("visual_grammar@2026-10-27.1", BOOK.version)
        import json
        data = json.loads((ROOT / "bie/brain/rulebook/visual_grammar.json").read_text(encoding="utf-8"))
        self.assertEqual(data["version"], "2026-10-27.1")
        self.assertTrue(any(c.startswith("2026-10-27.1") and "source packet" in c for c in data["changes"]))
        self.assertIn("source-listed", data["wording"]["W-01"]["english"])


if __name__ == "__main__":
    unittest.main()
