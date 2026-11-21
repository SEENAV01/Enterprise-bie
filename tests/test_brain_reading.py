"""BIE's code reader (bie/brain/reading.py; Navin, 21 November 2026: "book ko dekh bhi sake book understanding ke liye").

The Chapter 11 audit (NCERT Class 11 Biology, Photosynthesis) found what the text layer loses: the 2 of CO2 and the 3 and
4 of C3 and C4 came out as lines of their own, two columns on one printed line were read as one sentence, and a figure's
words (Z scheme: "Photosystem II") sat inside the running text. These tests build small PDFs by hand (Helvetica, no
library) with the same layouts and check the reader puts each right, and that the studio's book lines follow it.
"""
from __future__ import annotations

import unittest

from bie.brain import reading, studio
from bie.brain.pages import Block, Page, load_pages


def make_pdf(pages, width=612, height=792):
    """A PDF with one Helvetica text object per (x, baseline y, size, text) and a curve per (x0, y0, x1, y1) box;
    y counts from the bottom of the page, as in PDF."""
    objects = []

    def add(body):
        objects.append(body)
        return len(objects)

    font = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids, content_ids = [], []
    for page in pages:
        ops = []
        for x, y, size, text in page.get("text", []):
            safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"BT /F1 {size} Tf {x} {y} Td ({safe}) Tj ET")
        for x0, y0, x1, y1 in page.get("curves", []):
            ops.append(f"{x0} {y0} m {x0} {y1} {x1} {y0} {x1} {y1} c S")
        stream = "\n".join(ops).encode("latin-1")
        content_ids.append(add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"))
        page_ids.append(add(None))
    pages_id = add(None)
    for pid, cid in zip(page_ids, content_ids):
        objects[pid - 1] = (b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] /Contents %d 0 R "
                            b"/Resources << /Font << /F1 %d 0 R >> >> >>" % (pages_id, width, height, cid, font))
    objects[pages_id - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        b" ".join(b"%d 0 R" % p for p in page_ids), len(page_ids))
    catalog = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_id)
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, catalog, xref)
    return bytes(out)


def blocks_of(pdf, **kwargs):
    return load_pages(pdf, with_images=False, **kwargs)[2]


PARAGRAPH = ["The description of structure and variation of living",
             "organisms over a period of time ended up as two",
             "apparently irreconcilable perspectives on biology. The",
             "two perspectives rested on two levels of organisation.",
             "One described the organism and the other its cells."]


class Subscripts(unittest.TestCase):
    def test_the_2_of_co2_goes_back_after_its_o(self):
        pdf = make_pdf([{"text": [(60, 700, 10.5, "absorbs CO"), (121.6, 697.5, 6.1, "2"),
                                  (125.2, 700, 10.5, ") while the other half is out."),
                                  (60, 686, 10.5, "This showed that CO"), (165.0, 683.5, 6.1, "2"),
                                  (170.0, 686, 10.5, "was required for it.")]}])
        page = blocks_of(pdf)[0]
        texts = [b.text for b in page.blocks]
        self.assertEqual(texts, ["absorbs CO₂) while the other half is out.", "This showed that CO₂ was required for it."])
        self.assertEqual(len(page.absorbed), 2)              # both marks-only lines went back into their lines
        self.assertTrue(any("subscripts" in note for note in page.reading))

    def test_without_the_reader_the_text_layer_is_unchanged(self):
        pdf = make_pdf([{"text": [(60, 700, 10.5, "absorbs CO"), (121.6, 697.5, 6.1, "2"),
                                  (125.2, 700, 10.5, ") while the other half is out.")]}])
        texts = [b.text for b in blocks_of(pdf, read=False)[0].blocks]
        self.assertEqual(texts, ["absorbs CO ) while the other half is out.", "2"])

    def test_a_page_that_does_not_match_the_text_layer_is_kept_as_it_was(self):
        import io
        import pdfplumber
        pdf = make_pdf([{"text": [(60, 700, 10.5, "A line of the page.")]}])
        with pdfplumber.open(io.BytesIO(pdf)) as opened:
            read = reading.read_page(opened.pages[0], 1, [("p0001-b0001", "Some other text", (0, 0, 1, 1))])
        self.assertFalse(read.repaired)
        self.assertEqual([(p.id, p.text) for p in read.pieces], [("p0001-b0001", "Some other text")])


class Columns(unittest.TestCase):
    def test_a_side_list_beside_a_paragraph_is_read_after_it(self):
        side = ["Chapter 11", "Photosynthesis", "Chapter 12", "Respiration", "Chapter 13"]
        text = []
        for n, (left, right) in enumerate(zip(side, PARAGRAPH)):
            y = 600 - 13 * n
            text += [(60, y, 10, left), (200, y, 10, right)]
        blocks = blocks_of(make_pdf([{"text": text}]))[0].blocks
        kinds = [(b.kind, b.text) for b in blocks]
        self.assertEqual([t for k, t in kinds if k == "aside"], side)
        self.assertEqual([t for k, t in kinds if k == "text"], PARAGRAPH)
        self.assertLess(max(i for i, (k, _) in enumerate(kinds) if k == "text"),
                        min(i for i, (k, _) in enumerate(kinds) if k == "aside"))
        lines = studio.book_lines([blocks_of(make_pdf([{"text": text}]))[0]], [b.id for b in blocks])
        self.assertFalse(any("Chapter" in l["text"] and "organisms" in l["text"] for l in lines))
        self.assertIn("Chapter 11 Photosynthesis", [l["text"] for l in lines])   # a side entry is one book line

    def test_a_numbered_list_item_is_not_two_columns(self):
        rows = ["Parenchyma tissue is found in stems and roots.", "Collenchyma gives the plant mechanical strength.",
                "Sclerenchyma has thick dead cells with lignin."]
        text = []
        for n, row in enumerate(rows):
            text += [(77, 600 - 14 * n, 10, f"{n + 1}."), (100, 600 - 14 * n, 10, row)]
        blocks = blocks_of(make_pdf([{"text": text}]))[0].blocks
        self.assertEqual([b.text for b in blocks], [f"{n + 1}. {row}" for n, row in enumerate(rows)])
        self.assertEqual({b.kind for b in blocks}, {"text"})


class Figures(unittest.TestCase):
    def test_a_figures_words_on_a_text_line_are_kept_out_of_the_sentence(self):
        body = ["This movement of electrons is downhill, in", "terms of an oxidation-reduction or redox", "potential scale.",
                "The electrons are passed on to the pigments", "of photosystem PS I."]
        words = ["Photosystem II", "acceptor", "NADPH", "Electron", "LHC"]
        text = []
        for n, (line, word) in enumerate(zip(body, words)):
            y = 640 - 14 * n
            text += [(60, y, 10.5, line), (340, y, 10.5, word)]
        curves = [(330 + 30 * i, 560, 350 + 30 * i, 660) for i in range(6)]
        page = blocks_of(make_pdf([{"text": text, "curves": curves}]))[0]
        self.assertEqual([b.text for b in page.blocks if b.kind == "label"], words)
        lines = studio.book_lines([page], [b.id for b in page.blocks])
        self.assertFalse(any(word in l["text"] for l in lines for word in ("Photosystem", "NADPH", "LHC")))
        self.assertIn("This movement of electrons is downhill, in terms of an oxidation-reduction or redox potential scale.",
                      [l["text"] for l in lines])


class Kinds(unittest.TestCase):
    def test_a_running_head_repeats_and_a_high_body_line_does_not(self):
        pages = []
        for n in range(3):
            lines = [(84, 770, 7.7, f"PHOTOSYNTHESIS IN HIGHER PLANTS {135 + n}")]
            if n == 0:
                lines.append((60, 745, 10.5, "A body line that starts high on the page and is no head."))
            lines += [(60, 600 - 14 * i, 10.5, "Text of the page that goes on for a while here.") for i in range(3)]
            pages.append({"text": lines})
        read = blocks_of(make_pdf(pages))
        self.assertEqual([b.kind for b in read[0].blocks[:2]], ["running", "text"])
        self.assertEqual([b.kind for p in read for b in p.blocks if "PHOTOSYNTHESIS" in b.text], ["running"] * 3)

    def test_a_section_heading_is_a_book_line_of_its_own(self):
        page = blocks_of(make_pdf([{"text": [(60, 650, 12, "11.6.1 Splitting of Water"),
                                             (60, 630, 10.5, "You would then ask, how does PS II supply electrons"),
                                             (60, 616, 10.5, "continuously? The electrons must be replaced.")]}]))[0]
        self.assertEqual(page.blocks[0].kind, "heading")
        lines = [l["text"] for l in studio.book_lines([page], [b.id for b in page.blocks])]
        self.assertEqual(lines[0], "11.6.1 Splitting of Water")
        self.assertTrue(lines[1].startswith("You would then ask"))

    def test_headings_and_figure_words_need_no_question(self):
        page = Page(1, (Block("p0001-b0001", "11.6 THE ELECTRON TRANSPORT AND THE WAY IT RUNS DOWN THE THYLAKOID", (0, 0, 1, 1),
                              "heading"),
                        Block("p0001-b0002", "Photosystem II and photosystem I with their acceptors, a long label", (0, 0, 1, 1),
                              "label"),
                        Block("p0001-b0003", "In photosystem II the reaction centre chlorophyll a absorbs 680 nm light.",
                              (0, 0, 1, 1))))
        self.assertEqual(list(studio.teachable([page])), ["p0001-b0003"])


class PlansMadeBefore(unittest.TestCase):
    def test_an_old_plans_ids_keep_their_lines(self):
        page = Page(1, (Block("p0001-b0001", "Chapter 11", (0, 0.1, 0.2, 0.12), "aside"),
                        Block("p0001-b0001.2", "Plants make their food from carbon dioxide and water in light.",
                              (0.3, 0.1, 0.9, 0.12)),
                        Block("p0001-b0003", "Figure 11.1 A leaf in light", (0, 0.5, 0.5, 0.52), "caption"),
                        Block("p0001-b0005", "CO₂ + H₂O —Light→ [CH₂O] + O₂", (0, 0.6, 0.5, 0.62), "equation")),
                    absorbed=(("p0001-b0002", "p0001-b0001.2"), ("p0001-b0004", "p0001-b0003")))
        lines = [l["text"] for l in studio.book_lines([page], ["p0001-b0001", "p0001-b0004", "p0001-b0005"])]
        self.assertEqual(lines, ["Chapter 11", "Plants make their food from carbon dioxide and water in light.",
                                 "Figure 11.1 A leaf in light", "CO₂ + H₂O —Light→ [CH₂O] + O₂"])

    def test_the_chapter_text_names_each_kind_for_the_maker(self):
        page = Page(1, (Block("p0001-b0001", "11.2 EARLY EXPERIMENTS", (0, 0, 1, 1), "heading"),
                        Block("p0001-b0002", "Photosystem II", (0, 0, 1, 1), "label"),
                        Block("p0001-b0003", "Priestley showed that plants restore the air.", (0, 0, 1, 1))))
        text = studio.chapter_text([page])
        self.assertIn("[p0001-b0001] (heading) 11.2 EARLY EXPERIMENTS", text)
        self.assertIn("[p0001-b0002] (a figure's words, not running text) Photosystem II", text)
        self.assertIn("[p0001-b0003] Priestley showed", text)


class Structure(unittest.TestCase):
    def test_the_chapters_sections_and_zones_come_from_its_headings(self):
        def b(i, text, kind="text"):
            return Block(f"p0001-b{i:04d}", text, (0, 0, 1, 1), kind)
        page = Page(1, (b(1, "PHOTOSYNTHESIS IN HIGHER PLANTS 139", "running"), b(2, "Plants make food."),
                        b(3, "11.6 THE ELECTRON TRANSPORT", "heading"), b(4, "Electrons move downhill."),
                        b(5, "11.6.1 Splitting of Water", "heading"), b(6, "Water is split."),
                        b(7, "11.1 What do we Know?", "aside"), b(8, "SUMMARY", "heading"), b(9, "Plants make food in light."),
                        b(10, "EXERCISES", "heading"), b(11, "1. By looking at a plant can you tell C3 or C4?")))
        found = reading.chapter_structure([page])
        self.assertEqual([(h["number"], h["zone"]) for h in found["headings"]],
                         [("11.6", "body"), ("11.6.1", "body"), ("", "summary"), ("", "exercise")])
        where = found["of_block"]
        self.assertEqual(where["p0001-b0002"]["section"], "")
        self.assertEqual(where["p0001-b0004"]["section"], "11.6")
        self.assertEqual((where["p0001-b0006"]["section"], where["p0001-b0006"]["title"]), ("11.6.1", "Splitting of Water"))
        self.assertEqual(where["p0001-b0007"]["section"], "11.6.1")      # a contents entry in a side column is no heading
        self.assertEqual(where["p0001-b0009"]["zone"], "summary")
        self.assertEqual(where["p0001-b0011"]["zone"], "exercise")
        self.assertNotIn("p0001-b0001", where)

    def test_section_one_places_every_item_and_checks_its_role(self):
        from bie.brain import understanding
        items = {"p001-i1": {"page": 1, "block_ids": ["p0001-b0004"]}, "p001-i2": {"page": 1, "block_ids": []},
                 "p001-i3": {"page": 1, "block_ids": ["p0001-b0011"]}}
        of_block = {"p0001-b0004": {"section": "11.6", "title": "THE ELECTRON TRANSPORT", "zone": "body"},
                    "p0001-b0011": {"section": "11.10.4", "title": "Exercises", "zone": "exercise"}}
        understanding._place_in_sections(items, of_block)
        self.assertEqual([(i["ncert_section"], i["zone"]) for i in items.values()],
                         [("11.6", "body"), ("11.6", "body"), ("11.10.4", "exercise")])   # an image item follows the one before
        self.assertIn("exercise", understanding.ROLES)
        self.assertEqual(understanding.ITEM_SCHEMA["properties"]["role"]["enum"], understanding.ROLES)


if __name__ == "__main__":
    unittest.main()
