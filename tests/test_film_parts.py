"""Parts of an AI picture that move (Navin, 23 November 2026, routeS: "pressure moving rotating khulna band hona jaise
nigalna pakdna kisi jagah par chipkana"): the cutter's cleaning, checks, layers and plates (bie/brain/picture_parts.py,
with a fake SAM), the film's parts and acts and their checks, the layout checker pointing at parts, the player data, and
the films section's cutting step with a fake cutting environment. Offline; torch is never needed."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import vm_studio  # noqa: E402
from bie.brain import picture_parts, studio_film  # noqa: E402
from bie.model_gateway.live.messages import strict_ready  # noqa: E402

try:
    import scipy  # noqa: F401
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


def rect(h, w, x0, y0, x1, y1):
    m = np.zeros((h, w), dtype=bool)
    m[y0:y1, x0:x1] = True
    return m


class FakeCutter:
    """SAM stand-in: the mask is the pointed box (or a small square round the first point), with a fixed score."""

    def __init__(self):
        self.asked = []

    def look(self, image):
        self.size = image.size

    def mask(self, inside, outside, box):
        self.asked.append({"inside": inside, "outside": outside, "box": box})
        w, h = self.size
        if box:
            x0, y0, x1, y1 = box
        else:
            x, y = inside[0]
            x0, y0, x1, y1 = x - 2, y - 3, x + 2, y + 3
        return rect(h, w, int(x0 * w / 100), int(y0 * h / 100), int(x1 * w / 100), int(y1 * h / 100)), 0.9 if box else 0.8


def picture(w=200, h=100):
    a = np.zeros((h, w, 3), dtype=np.uint8)
    a[..., 0] = np.linspace(0, 255, w, dtype=np.uint8)[None, :]
    a[..., 1] = 120
    return Image.fromarray(a, "RGB")


class Cutter(unittest.TestCase):
    def test_clean_keeps_the_pointed_pieces_and_fills_holes(self):
        m = rect(50, 100, 5, 5, 30, 30) | rect(50, 100, 60, 10, 90, 40)
        m[15:20, 15:20] = False                                   # a hole in the first piece
        kept = picture_parts.clean(m, [[8, 16]])                  # a point on the first piece (x, y in percent)
        if not HAVE_SCIPY:                                        # without scipy the cut stays as SAM gave it
            self.assertTrue((kept == m).all())
            return
        self.assertTrue(kept[17, 17])                             # its hole is filled
        self.assertFalse(kept[20, 70])                            # the other piece is gone
        both = picture_parts.clean(m, [[8, 16], [75, 50]])        # a molecule: every pointed ball stays
        self.assertTrue(both[20, 70])
        molecule = picture_parts.clean(m, [[8, 16]], holes=False)
        self.assertFalse(molecule[17, 17])                        # a molecule's gaps stay open

    def test_check_cut_names_what_is_wrong(self):
        h, w = 100, 200
        self.assertIn("speck", picture_parts.check_cut(rect(h, w, 0, 0, 1, 1), [[0, 0]], None)[0])
        self.assertIn("background", picture_parts.check_cut(rect(h, w, 0, 0, 200, 60), [[10, 10]], None)[0])
        part = rect(h, w, 20, 20, 60, 60)
        self.assertEqual(picture_parts.check_cut(part, [[20, 40]], [10, 20, 30, 60]), [])
        self.assertIn("pointed points", picture_parts.check_cut(part, [[80, 80], [90, 90]], None)[0])
        self.assertIn("away from the box", picture_parts.check_cut(part, [[20, 40]], [70, 70, 95, 95])[0])

    def test_layer_is_the_part_alone_where_it_was(self):
        image = picture()
        mask = rect(100, 200, 40, 20, 80, 60)
        crop, box = picture_parts.layer(image, mask, pad=0)
        self.assertEqual(crop.mode, "RGBA")
        self.assertEqual(box, [20.0, 20.0, 40.0, 60.0])
        self.assertEqual(crop.getpixel((20, 20))[3], 255)         # inside the part: solid
        self.assertEqual(crop.getpixel((20, 20))[:3], image.getpixel((60, 40)))

    def test_layer_paints_over_what_the_part_holds(self):
        image = np.array(picture())
        image[35:45, 55:65] = (0, 0, 255)                         # a blue molecule in the part's pocket
        mask = rect(100, 200, 40, 20, 80, 60) & ~rect(100, 200, 55, 35, 65, 45)
        crop, box = picture_parts.layer(Image.fromarray(image), mask, pad=0,
                                        inner=rect(100, 200, 55, 35, 65, 45))
        r, g, b, a = crop.getpixel((20, 20))
        self.assertEqual(a, 255)
        self.assertLess(b, 100)                                   # filled from the part, not the blue molecule

    def test_fill_and_plate(self):
        rgb = np.zeros((40, 40, 3), dtype=np.uint8)
        rgb[:, :20] = 200
        rgb[:, 20:] = 100
        hole = rect(40, 40, 15, 15, 25, 25)
        filled = picture_parts.fill(rgb, hole)
        self.assertTrue((filled[~hole] == rgb[~hole]).all())      # known pixels keep their colour
        self.assertTrue(100 <= int(filled[20, 20, 0]) <= 200)     # the hole takes its surroundings' colour
        plated = np.asarray(picture_parts.plate(Image.fromarray(rgb), [hole], grow=2))
        self.assertLess(int(plated[20, 20, 0]), int(filled[20, 20, 0]))   # shaded: what a part uncovers lies in shadow
        self.assertTrue((plated[0, 0] == rgb[0, 0]).all())

    def test_cut_shot_layers_plate_and_order(self):
        cutter = FakeCutter()
        parts = [{"id": "beta", "inside": [[50, 50]], "outside": [[20, 50]], "box": [40, 30, 70, 80], "moves": True},
                 {"id": "adp", "inside": [[55, 50]], "outside": [], "box": [50, 40, 60, 60], "moves": False, "molecule": True},
                 {"id": "lost", "inside": [], "outside": [], "box": [], "moves": True}]
        done = picture_parts.cut_shot(picture(), parts, cutter)
        rows = {r["id"]: r for r in done["layers"]}
        self.assertEqual(rows["lost"]["problems"], ["the part was not found in the picture"])
        self.assertEqual(rows["beta"]["problems"], [])
        self.assertEqual([r["id"] for r in done["layers"]][:2], ["beta", "adp"])      # big parts first, held parts on top
        self.assertIsNotNone(done["plate"])                        # beta moves away, so the picture gets a plate
        molecule_asks = [a for a in cutter.asked if a["inside"] == [[55, 50]]]
        self.assertTrue(molecule_asks and all(a["box"] is None for a in molecule_asks))   # a molecule never with its box
        self.assertTrue(any(a["box"] for a in cutter.asked if a["inside"] == [[50, 50]]))
        self.assertTrue(any(not a["outside"] for a in cutter.asked if a["inside"] == [[50, 50]]))
        self.assertTrue(all([20, 50] not in a["outside"] or a["inside"] == [[50, 50]] for a in cutter.asked))

    def test_no_moving_part_no_plate(self):
        done = picture_parts.cut_shot(picture(), [{"id": "ring", "inside": [[50, 50]], "box": [30, 30, 70, 70],
                                                   "moves": False}], FakeCutter())
        self.assertIsNone(done["plate"])
        self.assertEqual(done["layers"][0]["problems"], [])

    def test_worker_reports_a_failed_cutter_and_writes_layers(self):
        import picture_parts_worker
        old = picture_parts.Sam2Cutter

        def broken(*args, **kwargs):
            raise RuntimeError("no torch here")
        with tempfile.TemporaryDirectory() as folder:
            pic, req, res = Path(folder) / "s1.png", Path(folder) / "req.json", Path(folder) / "res.json"
            picture().save(pic)
            req.write_text(json.dumps({"out": folder, "shots": [{"id": "s1", "image": str(pic), "parts": [
                {"id": "ring", "inside": [[50, 50]], "outside": [], "box": [30, 30, 70, 70], "moves": True}]}]}))
            try:
                picture_parts.Sam2Cutter = broken
                self.assertEqual(picture_parts_worker.main(["--request", str(req), "--result", str(res)]), 1)
                self.assertIn("no torch here", json.loads(res.read_text())["error"])
                picture_parts.Sam2Cutter = lambda *args, **kwargs: FakeCutter()
                self.assertEqual(picture_parts_worker.main(["--request", str(req), "--result", str(res)]), 0)
            finally:
                picture_parts.Sam2Cutter = old
            shot = json.loads(res.read_text())["shots"][0]
            self.assertTrue(Path(shot["layers"][0]["file"]).exists())
            self.assertTrue(Path(shot["plate"]).exists())
            self.assertEqual(shot["layers"][0]["problems"], [])

    def test_pinned_model(self):
        self.assertEqual(picture_parts.MODEL, "facebook/sam2.1-hiera-tiny")
        self.assertRegex(picture_parts.REVISION, r"^[0-9a-f]{40}$")
        self.assertIn("Apache-2.0", picture_parts.LICENCE)


def acts_film():
    """One cutaway of ATP synthase's head from above, with the routeS acts."""
    def line(roman, acts, part="concept"):
        return {"roman": roman, "voice": "देखिए " + roman, "pins": [], "arrows": [], "effects": [], "focus": [],
                "zoom": {"x": 50, "y": 50, "scale": 1.0}, "moves": [], "grows": [], "fuses": [], "reacts": [], "cycles": [],
                "acts": acts, "step": 0, "count": {"x": 50, "y": 86, "groups": [], "then": []}, "teaches": [], "beyond": "",
                "part": part}
    act = lambda part, do, toward=(), turns=0, rider="": {"part": part, "do": do, "toward": list(toward), "turns": turns,
                                                          "rider": rider}
    return {"title": "ATP synthase", "look": "glossy violet heads, copper stalk, warm stroma light, calm dark background",
            "shots": [{"id": "s1", "title": "Upar se", "key": "Ghoomti dandi beta ko kholti aur kasti hai", "covers": [0],
                       "visual": {"type": "cutaway", "svg": "", "library": "",
                                  "image_prompt": "Top view of ATP synthase head: a copper central stalk in the middle, "
                                                  "three pink beta lobes around it with open pockets, a small ADP and "
                                                  "phosphate molecule group in the top pocket",
                                  "parts": [{"id": "stalk", "name": "dandi", "looks": "copper central stalk in the middle"},
                                            {"id": "beta_top", "name": "beta", "looks": "pink beta lobe at the top"},
                                            {"id": "adp_pi", "name": "ADP aur Pi", "looks": "small molecule group in the top pocket"}]},
                       "dive": {"x": -1, "y": -1}, "aside": False,
                       "sentences": [line("Kya aapne socha yeh dandi kyun ghoomti hai?", [act("stalk", "turn", turns=-120)]),
                                     line("Dandi ke ghoomne se beta kasta hai aur ADP aur Pi dabkar jud jaate hain.",
                                          [act("stalk", "turn", turns=-120), act("beta_top", "tight", [47, 45]),
                                           act("adp_pi", "stick", [50, 22])]),
                                     line("Ab beta phir khulta hai.", [act("beta_top", "open", [47, 45])])]}]}


class FilmParts(unittest.TestCase):
    def test_schemas_stay_strict(self):
        self.assertTrue(strict_ready(studio_film.SCHEMA))
        self.assertTrue(strict_ready(studio_film.PLACE_SCHEMA))

    def test_instructions_teach_the_acts(self):
        text = studio_film.messages({"id": "q", "question": "?", "points": []}, course="Biology", language="Hinglish")[0]["content"]
        for word in ("MACHINE PARTS THAT MOVE", "visual.parts", "tight", "stick", "leave", "toward"):
            self.assertIn(word, text)

    def test_good_acts_pass(self):
        self.assertEqual(studio_film.parts_problems(acts_film()), [])

    def test_bad_acts_are_named(self):
        made = acts_film()
        shot = made["shots"][0]
        lines = shot["sentences"]
        lines[0]["acts"][0]["turns"] = 0                                       # a turn with no degrees
        lines[1]["acts"][1]["toward"] = []                                     # tight with nowhere to close
        lines[2]["acts"].append({"part": "gamma", "do": "glow", "toward": [], "turns": 0, "rider": ""})   # unknown part
        lines[2]["acts"].append({"part": "adp_pi", "do": "leave", "toward": [90, 90], "turns": 0, "rider": "H+"})
        shot["visual"]["parts"].append({"id": "ring", "name": "c ring", "looks": "a teal rotor wheel below"})
        said = " ".join(studio_film.parts_problems(made))
        for found in ("turn on 'stalk' needs turns", "tight on 'beta_top' needs toward", "'gamma', which this shot",
                      "only spin takes a rider", "'ADP aur Pi' leaves here but the line does not name it",
                      "part 'ring' is listed but nothing happens", "part 'ring' (c ring) is not drawn"):
            self.assertIn(found, said)

    def test_parts_only_on_pictures_and_a_said_motion_is_shown(self):
        made = acts_film()
        made["shots"][0]["visual"]["type"] = "diagram"
        self.assertIn("cut from an AI picture", " ".join(studio_film.parts_problems(made)))
        made = acts_film()
        made["shots"][0]["sentences"][2]["acts"] = []
        self.assertIn("'khul", " ".join(studio_film.parts_problems(made)))

    def test_acts_count_as_motion_and_mechanism(self):
        self.assertTrue(studio_film.moves(acts_film()["shots"][0]["sentences"][2]))
        self.assertEqual([p for p in studio_film.mechanism_problems(acts_film()) if "turn" in p], [])

    def test_place_points_at_parts_and_toward(self):
        made = acts_film()
        shot = made["shots"][0]
        items = studio_film.place_items(shot)
        self.assertIn("s1.act1", [i["id"] for i in items])                      # tight's point is checked on the picture
        answer = {"items": [{"id": "s1.act1", "points": [[48, 40]], "visible": True}],
                  "parts": [{"id": "stalk", "inside": [[47, 45], [48, 50]], "outside": [[30, 50]], "box": [40, 35, 55, 60], "visible": True},
                            {"id": "beta_top", "inside": [[50, 15]], "outside": [], "box": [40, 2, 60, 30], "visible": True},
                            {"id": "adp_pi", "inside": [], "outside": [], "box": [], "visible": False},
                            {"id": "stranger", "inside": [[5, 5]], "outside": [], "box": [1, 1, 9, 9], "visible": True}]}

        class Client:
            def chat(self, *, model, messages, schema=None):
                self.text = messages[1]["content"][0]["text"]
                return {"content": json.dumps(answer), "usage": {}}
        client = Client()
        got = studio_film.place(client, "m", shot, None, {"type": "image"})
        self.assertIn("The parts BIE will cut out and move", client.text)
        self.assertEqual(sorted(got["parts"]), ["beta_top", "stalk"])          # the unseen part and a stranger are dropped
        self.assertEqual(shot["sentences"][1]["acts"][1]["toward"], [48.0, 40.0])
        wanted = {w["id"]: w for w in studio_film.part_requests(shot, got["parts"])}
        self.assertTrue(wanted["stalk"]["moves"] and wanted["beta_top"]["moves"])
        self.assertFalse(wanted["stalk"]["molecule"])
        self.assertTrue(studio_film._molecule_part({"id": "adp_pi", "name": "ADP aur Pi"}))

    def test_player_data_carries_parts_and_times_acts(self):
        made = acts_film()
        layers = {"s1": [{"id": "stalk", "img": "data:image/webp;base64,AA", "box": [40, 35, 55, 60], "centre": [47, 47]},
                         {"id": "beta_top", "img": "data:image/webp;base64,AA", "box": [40, 2, 60, 30], "centre": [50, 15]}]}
        data = studio_film.player_data(made, images={}, audio={}, chapter="c", question={"id": "q"}, parts=layers)
        shot = data["shots"][0]
        self.assertEqual([p["id"] for p in shot["parts"]], ["stalk", "beta_top"])
        second = shot["sentences"][1]["acts"]
        self.assertEqual([a["part"] for a in second], ["stalk", "beta_top"])   # adp_pi was not cut, so it does not act
        self.assertGreaterEqual(second[0]["at"], 0.3)
        timed = studio_film.act_times([{"part": "a"}, {"part": "b"}], {"a": "dandi", "b": "beta"},
                                      "Pehle beta, phir dandi ghoomti hai aur beta kasta hai.", 6.0)
        self.assertGreaterEqual(timed[1]["at"] - timed[0]["at"], 1.2)          # one thing at a time
        self.assertLessEqual(timed[1]["at"], 6.0 - 1.6)

    def test_moving_parts_are_drawn_solid(self):
        shot = acts_film()["shots"][0]
        prompt = studio_film.image_prompt(shot, "glossy violet heads")
        self.assertIn("solid and opaque", prompt)
        self.assertIn("dandi (copper central stalk in the middle)", prompt)
        shot["sentences"] = [dict(s, acts=[]) for s in shot["sentences"]]
        self.assertNotIn("solid and opaque", studio_film.image_prompt(shot, "glossy violet heads"))

    def test_review_page_lists_every_act(self):
        page = studio_film.acts_page(acts_film(), {"wanted": 3, "cut": 1, "parts": {
            "s1.stalk": {"area": 2.1, "problems": []}, "s1.beta_top": {"area": 0.01, "problems": ["the cut is a speck"]}}},
            question={"id": "q", "question": "ATP kaise banta hai?"})
        for said in ("dandi ghoomta hai (-120°)", "beta kasta hai (dabaav)", "ADP aur Pi khisak kar judta hai",
                     "saaf nahi kata: the cut is a speck", "nahi kata (tasveer mein nahi mila)", "1 / 3"):
            self.assertIn(said, page)

    def test_player_moves_parts(self):
        html = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for name in ("function doAct", "function partsReplay", "function pressure", "function bond", "function ridersStep",
                     "kind:'act'", "p-spin"):
            self.assertIn(name, html)

    def test_a_far_close_travels_before_it_presses(self):
        # 11.6.1 on the VM (23 November 2026): "Supply box band ho jaaye" put tight on a lid lying 30% below its box; the
        # jaw pulsed where the lid lay and the box never closed. A point beyond the part's reach is now reached by travel.
        html = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn("function beyondReach(P,T)", html)
        act = html[html.index("function doAct"):html.index("function addRiders")]
        travel = act.index("a.do==='tight'&&T&&beyondReach(P,T)")
        self.assertLess(travel, act.index("else if(POSE[a.do])"))             # tried before the jaw
        branch = act[travel:act.index("else if(POSE[a.do])")]
        for said in ("to.tx=T[0]-P.c[0]", "to.ty=T[1]-P.c[1]", "pressure(T,"):
            self.assertIn(said, branch)


class SectionCutting(unittest.TestCase):
    def test_cut_parts_reads_the_cutter(self):
        made = acts_film()
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            pic = folder / "s1.png"
            picture(400, 225).save(pic)
            placed = {"s1": {"parts": {"stalk": {"inside": [[47, 45]], "outside": [], "box": [40, 35, 55, 60]},
                                       "beta_top": {"inside": [[50, 15]], "outside": [], "box": [40, 2, 60, 30]}}}}
            calls = []

            def run(cmd, env=None, timeout=None, check=False):
                calls.append(cmd)
                request = json.loads(Path(cmd[cmd.index("--request") + 1]).read_text())
                shot = request["shots"][0]
                self.assertEqual([p["id"] for p in shot["parts"]], ["stalk", "beta_top"])
                Image.new("RGBA", (40, 40), (200, 100, 50, 255)).save(folder / "cut-stalk.png")
                picture(400, 225).save(folder / "cut-plate.png")
                Path(cmd[cmd.index("--result") + 1]).write_text(json.dumps({"error": None, "shots": [{
                    "id": "s1", "plate": str(folder / "cut-plate.png"),
                    "layers": [{"id": "stalk", "file": str(folder / "cut-stalk.png"), "box": [40, 35, 55, 60],
                                "centre": [47, 47], "area": 2.0, "score": 0.95, "problems": []},
                               {"id": "beta_top", "box": None, "area": 0.01, "score": 0.4, "problems": ["the cut is a speck"]}]}]}))

            layers, plates, report = vm_studio.cut_parts(made, placed, {"s1": pic}, folder / "parts", python=sys.executable,
                                                         run=run)
        self.assertEqual(len(calls), 1)
        self.assertEqual([p["id"] for p in layers["s1"]], ["stalk"])
        self.assertTrue(layers["s1"][0]["img"].startswith("data:image/webp;base64,"))
        self.assertIn("s1", plates)
        self.assertEqual((report["wanted"], report["cut"]), (3, 1))
        said = " ".join(report["problems"])
        self.assertIn("parts not found in the picture: adp_pi", said)
        self.assertIn("part beta_top not cut cleanly (the cut is a speck)", said)

    def test_no_cutting_environment_plays_uncut(self):
        made = acts_film()
        with tempfile.TemporaryDirectory() as folder:
            pic = Path(folder) / "s1.png"
            picture().save(pic)
            placed = {"s1": {"parts": {"stalk": {"inside": [[47, 45]], "outside": [], "box": [40, 35, 55, 60]}}}}
            old = vm_studio.parts_python
            vm_studio.parts_python = lambda: None
            try:
                layers, plates, report = vm_studio.cut_parts(made, placed, {"s1": pic}, Path(folder) / "parts")
            finally:
                vm_studio.parts_python = old
        self.assertEqual((layers, plates), ({}, {}))
        self.assertIn("not on this machine", " ".join(report["problems"]))

    def test_a_film_without_parts_never_calls_the_cutter(self):
        made = copy.deepcopy(acts_film())
        for s in made["shots"][0]["sentences"]:
            s["acts"] = []
        self.assertEqual(vm_studio.cut_parts(made, {}, {}, Path("/nonexistent"), run=lambda *a, **k: 1 / 0)[2]["wanted"], 0)


if __name__ == "__main__":
    unittest.main()
