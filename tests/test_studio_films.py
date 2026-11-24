"""The course studio, stage 2 (Navin, 18 November 2026): one film per approved question, checked by code (said = shown,
safe SVG, coverage of the question's points) and turned into a phone film. Offline: fake maker, fake pictures, fake voice."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import codex_vm  # noqa: E402
import vm_studio  # noqa: E402
from bie.brain import studio, studio_film, studio_script  # noqa: E402
from bie.brain.pages import Block, Page  # noqa: E402
from bie.model_gateway.live.messages import strict_ready  # noqa: E402

def png_bytes():
    import io
    from PIL import Image
    buffer = io.BytesIO()
    Image.new("RGB", (32, 18), (40, 120, 60)).save(buffer, "PNG")
    return buffer.getvalue()
QUESTION = {"id": "q01", "question": "Ek hi hawa kahin baadh aur kahin sookha kyun laati hai?", "hook": "Mumbai bheega, Pune sookha.",
            "points": [{"block_ids": ["p0001-b0002"], "point": "Hawa pahaad par chadhkar barasti hai", "kind": "process"},
                       {"block_ids": ["p0001-b0003"], "point": "Doosri taraf vrishti chhaya", "kind": "cause_effect"}],
            "film": {"length": "short", "showing_moment": "Hawa ka gola Ghat par chadhta hai"},
            "game_stage": {"mechanic": "drag_to_target", "idea": "Gole ko Ghat par kheencho"}}
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 56"><defs><linearGradient id="g"><stop offset="0"/>'
       '</linearGradient></defs><rect width="100" height="56" fill="#eef"/><path id="slope" d="M0 50 L50 10 L100 50"/>'
       '<circle id="cloud" cx="40" cy="12" r="6"/>' + "".join(f'<circle cx="{5 + i * 9}" cy="52" r="2"/>' for i in range(10))
       + '</svg>')


def sentence(roman, voice, pins=(), focus=(), moves=(), grows=(), fuses=(), scale=1.1):
    return {"roman": roman, "voice": voice, "pins": [{"label": p, "x": 40, "y": 30} for p in pins],
            "arrows": [{"points": [[10, 60], [40, 30]], "label": "hawa"}], "effects": [],
            "focus": list(focus), "zoom": {"x": 50, "y": 50, "scale": scale},
            "moves": list(moves), "grows": list(grows), "fuses": list(fuses)}


CLOUDS = {"what": "drop", "colour": "blue", "label": "hawa", "points": [[10, 80], [35, 45], [55, 25]], "count": 6,
          "ms": 2600, "loop": True}


def film():
    return {"title": "Ghat aur baarish", "look": "Monsoon greens, wet stone, soft grey light, low aerial camera", "shots": [
        {"id": "s1", "title": "Ghat ki deewar", "key": "Hawa chadhti hai, baarish hoti hai", "covers": [0],
         "visual": {"type": "photo", "image_prompt": "Photorealistic wide view of the green Western Ghats escarpment in the "
                    "July monsoon with dark clouds on the windward slope and waterfalls", "svg": ""},
         "dive": {"x": -1, "y": -1},
         "sentences": [sentence("Yeh Ghat ki deewar baarish kyun rokti hai? Aaiye jaante hain.", "यह घाट की दीवार बारिश क्यों रोकती है? आइए जानते हैं।", ["Ghat"]),
                       sentence("Hawa yahan chadhkar thandi hoti hai aur barasti hai.", "हवा यहाँ चढ़कर ठंडी होती है और बरसती है।",
                                moves=[CLOUDS], scale=1.8)]},
        {"id": "s2", "title": "Kaat", "key": "Doosri taraf sookha", "covers": [1],
         "visual": {"type": "diagram", "image_prompt": "", "svg": SVG},
         "dive": {"x": 55, "y": 25},
         "sentences": [sentence("Ab pahaad ka kaat dekhiye, baadal upar.", "अब पहाड़ का काट देखिए, बादल ऊपर।", ["baadal"], ["cloud"]),
                       sentence("Doosri taraf utarti hawa sookhi rehti hai.", "दूसरी तरफ़ उतरती हवा सूखी रहती है।", [], ["slope"],
                                moves=[dict(CLOUDS, label="", loop=False)])]}]}


class FakeClient:
    def __init__(self, answers):
        self.answers = list(answers)
        self.images = 0

    def chat(self, *, model, messages, schema=None):
        return {"content": json.dumps(self.answers.pop(0), ensure_ascii=False), "usage": {"input_tokens": 10, "output_tokens": 5}}

    def generate_image(self, prompt, out, model=None):
        assert "No text" in prompt
        self.images += 1
        Path(out).write_bytes(png_bytes())
        return {"file": Path(out).name}


class FakeVoice:
    def say(self, text):
        return {"uri": "data:audio/mpeg;base64,AAAA", "dur": 2.0}


class FilmChecks(unittest.TestCase):
    def test_schema_strict(self):
        self.assertTrue(strict_ready(studio_film.SCHEMA))

    def test_good_film_passes(self):
        self.assertEqual(studio_film.problems(film(), QUESTION), [])

    def test_pin_not_spoken_and_bad_svg_and_coverage(self):
        bad = film()
        bad["shots"][0]["sentences"][0]["pins"][0]["label"] = "Thar"
        bad["shots"][1]["visual"]["svg"] = '<svg viewBox="0 0 1 1"><script>alert(1)</script></svg>'
        bad["shots"][1]["covers"] = []
        found = " | ".join(studio_film.problems(bad, QUESTION))
        self.assertIn("not spoken", found)
        self.assertIn("banned element", found)
        self.assertIn("points 1", found)

    def test_devanagari_voice_needed(self):
        bad = film()
        bad["shots"][0]["sentences"][1]["voice"] = "Hawa chadhti hai"
        self.assertIn("Devanagari", " ".join(studio_film.problems(bad, QUESTION)))


class FilmMotion(unittest.TestCase):
    """Navin, 19 November 2026: the Campbell 17 film's motion (what travels is shown travelling, the camera pushes in)."""

    def test_motion_is_checked(self):
        bad = film()
        first = bad["shots"][0]["sentences"][1]
        first["moves"] = [dict(CLOUDS, points=[[10, 180]], count=40, ms=50, label="Thar")]
        first["grows"] = [{"points": [[5, 5]], "label": "", "ms": 100}]
        first["fuses"] = [{"x": 50, "y": 50, "label": ""}]
        first["zoom"]["scale"] = 3
        bad["shots"][0]["dive"] = {"x": 20, "y": 20}
        found = " | ".join(studio_film.problems(bad, QUESTION))
        for text in ("2 to 6 points", "count is 1 to 12", "ms is 800 to 8000", "'Thar' is not spoken", "2 to 8 points",
                     "grow's ms", "needs its label", "zoom.scale must be 1.0 to 2.2", "first shot cannot dive"):
            self.assertIn(text, found)

    def test_short_labels_are_spoken_by_their_names(self):
        # Q14 remake (20 November 2026): every 'H+' label on a move was refused though the sentence said protons
        def found(label, said):
            move = dict(CLOUDS, points=[[10, 10], [40, 40]], count=4, ms=2000, label=label)
            return " ".join(studio_film.motion_problems({"moves": [move]}, studio_film._tokens(said), "s1 sentence 1"))
        self.assertNotIn("not spoken", found("H+", "Protons lumen se stroma mein laut-te hain"))
        self.assertNotIn("not spoken", found("Pi", "ADP aur Pi CF1 tak aate hain"))
        self.assertNotIn("not spoken", found("CO2", "Rubisco CO2 ko pakadta hai"))
        self.assertIn("'H+' is not spoken", found("H+", "Paani neeche behta hai"))

    def test_a_film_without_motion_is_sent_back(self):
        still = film()
        for shot in still["shots"]:
            for line in shot["sentences"]:
                line["moves"], line["grows"], line["fuses"] = [], [], []
        self.assertIn("show what travels travelling", " ".join(studio_film.problems(still, QUESTION)))

    def test_player_plays_motion(self):
        page = Path(ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for hook in ("addMove", "addGrow", "addFuse", "camTo", "toScreen", "s.dive", "SPRITE_SCALE", "/*__FILM__*/null"):
            self.assertIn(hook, page)

    def test_player_keeps_diagram_words_readable(self):
        """The first Photosynthesis films (19 Nov 2026) showed three faults on diagram shots: a zoom cut words at the frame
        edge, highlighted words got a thick red outline, and moving sprites passed over words. The player now keeps the
        diagram's words on their own top layer, fades a word the frame cuts, and highlights words without an outline."""
        page = Path(ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn(".svg text.lit,.svg .lit text{stroke:none!important", page)
        self.assertNotIn(".svg .lit{filter:drop-shadow(0 0 6px #e8a93a);stroke", page)
        self.assertIn(".svg.base svg text{visibility:hidden}", page)
        self.assertIn(".svg.tl svg text.cut{opacity:0}", page)
        build = page[page.index("function build(i)"):page.index("function show(i,k,viaDive)")]
        self.assertIn("'svg base'", build)
        self.assertLess(build.index("worldLayers()"), build.index("textLayer()"))   # words go above the sprite layer
        layer = page[page.index("function textLayer()"):page.index("function edgeCut(now)")]
        self.assertIn("e.dataset.oid=e.id;e.removeAttribute('id')", layer)          # ids stay unique in the page
        self.assertIn("[data-oid=", page)                                           # a highlight reaches the top words
        self.assertIn("function tick(now){camStep(now);edgeCut(now);", page)
        self.assertIn("words:texts.length,cut:", page)

    def test_cutaway_is_an_ai_picture_in_cutaway_style(self):
        shot = {"visual": {"type": "cutaway", "image_prompt": "The inside of a mature ovule", "svg": ""}}
        self.assertIn("transparent cross-section", studio_film.image_prompt(shot, "", "glossy"))   # glossy (23 Nov 2026)
        self.assertIn("Realistic scientific render", studio_film.image_prompt(shot))   # his hybrid look again (24 Nov 2026)
        data = studio_film.player_data(film(), images={}, audio={}, chapter="Monsoon", question=QUESTION)
        self.assertEqual(data["shots"][1]["dive"], {"x": 55, "y": 25})
        self.assertIsNone(data["shots"][0]["dive"])
        self.assertEqual(data["shots"][0]["sentences"][1]["moves"][0]["what"], "drop")


REACT = {"inputs": [{"what": "CO2", "from": [10, 20]}, {"what": "RuBP", "from": [20, 80]}], "at": [50, 50],
         "outputs": [{"what": "3-PGA", "to": [70, 40]}, {"what": "3-PGA", "to": [70, 60]}], "label": "CO2 + RuBP → 3-PGA",
         "ms": 4000, "loop": False}
CALVIN = {"x": 55, "y": 50, "rx": 22, "ry": 30, "label": "Calvin cycle", "carriers": 2, "ms": 14000, "stations": [
    {"at": 300, "label": "fixation", "becomes": "3-PGA", "takes": ["CO2"], "gives": []},
    {"at": 90, "label": "reduction", "becomes": "G3P", "takes": ["ATP"], "gives": []},
    {"at": 200, "label": "regeneration", "becomes": "RuBP", "takes": [], "gives": []}]}
# the whole cycle in one wheel puts 8 different molecules on screen at once (the Q14 ending, 20 November 2026: "khichdi")
CALVIN_BUSY = dict(CALVIN, stations=[
    {"at": 300, "label": "fixation", "becomes": "3-PGA", "takes": ["CO2"], "gives": []},
    {"at": 90, "label": "reduction", "becomes": "G3P", "takes": ["ATP", "NADPH"], "gives": ["ADP", "NADP+", "G3P"]},
    {"at": 200, "label": "regeneration", "becomes": "RuBP", "takes": ["ATP"], "gives": ["ADP"]}])


def living_film():
    """A two-shot film in the living style: the stroma picture, a reaction and the Calvin cycle turning."""
    f = film()
    f["shots"][1]["visual"] = {"type": "cutaway", "image_prompt": "The inside of a chloroplast: stacked thylakoid discs at the "
                               "left, open fluid stroma in the centre and right, membranes with depth", "svg": ""}
    f["shots"][1]["sentences"] = [
        sentence("Stroma mein CO2 aata hai, par 3-PGA kaise banta hai? Dekhiye, RuBP se judkar 3-PGA banta hai.",
                 "स्ट्रोमा में CO2 आता है, पर 3-PGA कैसे बनता है? देखिए, RuBP से जुड़कर 3-PGA बनता है।"),
        sentence("Calvin cycle ghoomta hai: fixation, reduction aur regeneration.", "केल्विन साइकिल घूमता है: फ़िक्सेशन, रिडक्शन और रीजनरेशन।"),
        sentence("Fixation par CO2 judta hai aur 3-PGA banta hai.", "फ़िक्सेशन पर CO2 जुड़ता है और 3-PGA बनता है।"),
        sentence("Reduction par ATP lagta hai aur G3P banta hai.", "रिडक्शन पर ATP लगता है और G3P बनता है।"),
        sentence("Regeneration par RuBP wapas banta hai.", "रीजनरेशन पर RuBP वापस बनता है।")]
    f["shots"][1]["sentences"][0]["reacts"] = [dict(REACT)]
    f["shots"][1]["sentences"][1]["cycles"] = [dict(CALVIN)]
    return f


class LivingFilm(unittest.TestCase):
    """Navin, 20 November 2026, on the first three Photosynthesis films: they felt like slides, the stroma was a box with
    "CO2 fixation" written in it, and no voice reached him. One world, processes happening on AI pictures, molecules from
    BIE's kit, reactions and cycles seen happening, and a voice that plays."""

    def test_living_film_passes_and_carries_its_kit(self):
        self.assertEqual(studio_film.problems(living_film(), QUESTION), [])
        data = studio_film.player_data(living_film(), images={}, audio={}, chapter="Photosynthesis", question=QUESTION)
        self.assertEqual(set(data["kit"]["molecules"]), {"CO2", "RuBP", "3-PGA", "G3P", "ATP"})
        self.assertIn("C", data["kit"]["elements"])
        self.assertEqual(data["shots"][1]["sentences"][1]["cycles"][0]["stations"][1]["takes"], ["ATP"])

    def test_slides_are_sent_back(self):
        bad = film()
        bad["look"] = ""
        bad["shots"][0]["sentences"][0]["roman"] = "Yeh Ghat ki deewar hai."
        third = json.loads(json.dumps(bad["shots"][1]))
        third["id"], third["dive"] = "s3", {"x": -1, "y": -1}
        bad["shots"][1]["dive"] = {"x": -1, "y": -1}
        for line in third["sentences"]:
            line["moves"] = []
        bad["shots"].append(third)
        found = " | ".join(studio_film.problems(bad, dict(QUESTION, film={"length": "long", "showing_moment": "x"})))
        for text in ("2 shots cut instead of diving", "2 diagram shots", "first sentence must be the question",
                     "look is missing", "nothing moves in s3", "sentences move"):
            self.assertIn(text, found)

    def test_reacts_and_cycles_are_checked(self):
        bad = living_film()
        react = bad["shots"][1]["sentences"][0]["reacts"][0]
        react["inputs"] = react["inputs"] * 2
        react["ms"], react["label"] = 100, "Glucose sugar"
        cycle = bad["shots"][1]["sentences"][1]["cycles"][0]
        cycle.update(x=90, rx=30, carriers=9, ms=1000)
        cycle["stations"] = [dict(cycle["stations"][0], label="carboxylation", takes=["unobtainium"])]
        found = " | ".join(studio_film.problems(bad, QUESTION))
        for text in ("1 to 3 inputs", "react's ms is 1500 to 9000", "react label 'Glucose sugar' is not spoken",
                     "must sit inside the picture", "1 to 4 carriers", "one lap", "2 to 5 stations",
                     "must be sprites or kit molecules", "station label 'carboxylation' is not spoken"):
            self.assertIn(text, found)

    def test_kit_molecules_are_well_formed(self):
        kit = json.loads((ROOT / "bie" / "brain" / "molecule_kit.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(kit["molecules"]), 18)
        for name in ("ATP", "ADP", "NADPH", "NADP+", "CO2", "RuBP", "3-PGA", "G3P", "glucose", "H+", "H2O", "O2", "PEP", "OAA",
                     "malate", "pyruvate"):
            self.assertIn(name, kit["molecules"])
            self.assertIn(name, studio_film.ACTORS)
        for name, spec in kit["molecules"].items():
            for part in spec["parts"]:
                self.assertIn(part[0], "bargt", (name, part))
                if part[0] in "ar":
                    self.assertIn(part[1], kit["elements"], (name, part))
        carbons = lambda n: sum(1 for p in kit["molecules"][n]["parts"] if p[0] == "a" and p[1] == "C")
        self.assertEqual((carbons("RuBP"), carbons("3-PGA"), carbons("G3P"), carbons("OAA")), (5, 3, 3, 4))  # count the carbons

    def test_pictures_share_the_film_look(self):
        shot = {"visual": {"type": "cutaway", "image_prompt": "The inside of a chloroplast: thylakoids and stroma", "svg": ""}}
        prompt = studio_film.image_prompt(shot, "emerald thylakoids, amber stroma glow")
        self.assertIn("Same look as the other pictures of this film: emerald thylakoids", prompt)
        self.assertIn("No text", prompt)

    def test_a_structure_is_coloured_only_on_the_pictures_that_show_it(self):
        # Q14 remake (20 November 2026): "ATP synthase: violet CF1 head" in the shared look put ATP synthase on the cell
        # picture, one scale too early; its colours now go only to pictures whose prompt names it
        look = ("Continuous photoreal journey, 16:9, golden light aur teal shadows; leaf emerald, cells translucent jade, "
                "thylakoid membrane dark green; ATP synthase: amber CF0 ring, violet six-lobed CF1 head; proton pump copper, H+ gold")
        cell = {"visual": {"type": "cutaway", "image_prompt": "Mesophyll cell with chloroplasts along the wall. No molecular proteins."}}
        membrane = {"visual": {"type": "cutaway", "image_prompt": "The thylakoid membrane with ATP synthase and a proton pump."}}
        at_cell, at_membrane = studio_film.image_prompt(cell, look), studio_film.image_prompt(membrane, look)
        self.assertIn("golden light aur teal shadows", at_cell)
        self.assertIn("cells translucent jade", at_cell)
        for absent in ("ATP synthase", "proton pump", "thylakoid membrane", "H+"):
            self.assertNotIn(absent, at_cell)
        for present in ("ATP synthase: amber CF0 ring", "proton pump copper", "thylakoid membrane dark green", "golden light"):
            self.assertIn(present, at_membrane)
        self.assertNotIn("leaf emerald", at_membrane)

    def test_player_plays_living_films_and_the_voice(self):
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for hook in ("function molecule(name,parent)", "function addReact(", "function stepReact(", "function addCycle(",
                     "function stepCycle(", "f.type==='spin'", "classList.add('ghost')", "BIEVoice.play(", "BIEVoice.unlock()",
                     "/*__VOICE__*/", "id=\"vnote\"", "addReact(r,", "addCycle(c,", "voice:BIEVoice.state"):
            self.assertIn(hook, page)
        for gone in ("<audio", "blobURL", "au.play()"):
            self.assertNotIn(gone, page)
        voice = (ROOT / "bie" / "brain" / "studio_voice_player.js").read_text(encoding="utf-8")
        for hook in ("decodeAudioData", "createBufferSource", "el.play()", "set('blocked')", "ctx.resume()"):
            self.assertIn(hook, voice)
        play = voice[voice.index("async function play("):]
        self.assertLess(play.index("viaElement(uri"), play.index("viaContext(uri"))   # data: URI first, then Web Audio
        self.assertNotIn("createObjectURL", voice)                                   # no blob: URL a viewer can refuse

    def test_player_keeps_the_first_living_film_tidy(self):
        """What the first living film (Q14, 20 November 2026) showed: tags piled under the Calvin cycle, two ATPs for a
        moment after a react, the next picture growing as a box. The player now declutters tags every frame, hands a
        react's product over to the move that carries it on, fans a station's molecules out, and keeps the lens round."""
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        tick = page[page.index("function tick(now)"):page.index("requestAnimationFrame(tick);}")]
        self.assertIn("declutter(now)", tick)
        self.assertIn("g.mtag", page[page.index("function declutter("):])
        self.assertIn("{class:'mtag'}", page[page.index("function molecule("):page.index("function declutter(")])
        for who, level in (("q.becomes,'gold',wsvg),3)", "carrier"), ("sprite(m.what,m.colour,wsvg),1)", "move"),
                           ("sprite(w,'gold',wsvg),0)", "flyer")):
            self.assertIn(who, page, level)
        sentence = page[page.index("function sentence(k)"):page.index("function speak(")]
        self.assertLess(sentence.index("handOff(t.moves"), sentence.index("addMove(m,"))
        self.assertIn("o.goneAt&&now>=o.goneAt", page[page.index("function stepReact("):])
        cycle = page[page.index("function stepCycle("):page.index("function tick(")]
        self.assertIn("away(q,13+j*2,-1,j)", cycle)    # takes come in from the side the carrier comes from, fanned
        self.assertIn("away(q,12+j*2,1,j)", cycle)     # gives leave to the side it goes to, fanned
        show = page[page.index("function show("):page.index("function sentence(")]
        self.assertIn("camTo(50,50,1,ms*.78)", show)   # the picture fills the frame before the lens opens to the corners
        self.assertIn("lens(u<.78?18+ease(u/.78)*22:", show)

    def test_player_names_only_what_is_said_now(self):
        """Navin on 11.6.2a (23 November 2026, "steps clear na dikhe ... to kya khichdi pakti hai"): thirteen names stood on
        one line's picture, ATP, NADPH and O2 twice each (the molecule's own tag and a pin at the end of its move). A
        molecule that carries its name gets no second label. Navin on r2 of 11.6.3b (24 November 2026, "labelling bahut
        jyada kam ho gayi hai"): an earlier line's labels stay on the shot, quieter; eight at most, the oldest leave first."""
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        move = page[page.index("function addMove("):page.index("function addGrow(")]
        self.assertIn("m.label&&!tagSays(m.what,m.label)", move)
        self.assertIn("function tagSays(what,label)", page)
        self.assertIn("const MAX_LABELS=8;", page)
        add = page[page.index("function addLabel("):page.index("function placeLabels(")]
        self.assertIn("labels.length<=MAX_LABELS", add)
        self.assertIn("if(!l.math&&l.k<labelRound){l.box.classList.remove('new');l.box.classList.add('old');}", add)
        self.assertIn("same.box.classList.remove('old')", add)            # a name said again is bright again
        self.assertIn(".pin.old{", page)
        sentence = page[page.index("function sentence(k)"):page.index("function speak(")]
        self.assertLess(sentence.index("labelRound++;retireLabels();"), sentence.index("addLabel(p.t"))

    def test_maker_names_the_colours_of_repeated_structures(self):
        self.assertIn("names\n  the colour of every structure that is seen in more than one picture", studio_film.INSTRUCTIONS)


# --- every book line taught (Navin, 20 November 2026, on the first living film, Q14) -----------------------------------

def page(number, blocks):
    return Page(number=number, blocks=tuple(Block(id=f"p{number:04d}-b{i:04d}", text=text, box=box)
                                            for i, (text, box) in enumerate(blocks, 1)))


LINE = lambda y: (0.30, y, 0.90, y + 0.013)
PAGES = [
    page(11, [("PHOTOSYNTHESIS IN HIGHER PLANTS 141", (0.1, 0.10, 0.9, 0.11)),
              ("Figure 11.7 ATP synthesis through chemiosmosis", (0.1, 0.12, 0.5, 0.13)),
              ("Hence protons gather in the lumen and the pH", LINE(0.18)),
              ("falls. Why are we so interested in the proton gradient? The", LINE(0.20)),
              ("gradient is broken down when protons move to the stroma through the", LINE(0.22)),
              ("2024-25", (0.4, 0.95, 0.6, 0.96))]),
    page(12, [("142 BIOLOGY", (0.1, 0.10, 0.9, 0.11)),
              ("channel of the CF of the ATP synthase. Water splits as H O on the inner side.", LINE(0.15)),
              ("0", (0.405, 0.157, 0.41, 0.166)),
              ("The ATP is used to fix CO in the stroma.", (0.30, 0.20, 0.70, 0.213)),
              ("2", (0.543, 0.207, 0.548, 0.216))]),
]
WANTED = ["p0011-b0002", "p0011-b0004", "p0011-b0005", "p0012-b0002", "p0012-b0004"]


def taught_film(teaches, beyond=("",) * 4):
    """The Monsoon film reused with the book lines it teaches (only the bookkeeping matters here)."""
    f = film()
    f["shots"][0]["sentences"][1]["roman"] = "Hawa Ghats par chadhkar thandi hoti hai (cools) aur barasti hai."
    f["shots"][1]["sentences"][1]["roman"] = "Doosri side par utarti hawa sookhi rehti hai."
    lines = [s for shot in f["shots"] for s in shot["sentences"]]
    for s, n, b, part in zip(lines, teaches, beyond, ("hook", "concept", "prerequisite", "use")):
        s["teaches"], s["beyond"], s["part"] = list(n), b, part
    return f


BOOK_Q = dict(QUESTION, book_lines=[
    {"n": 1, "text": "The wind climbs the Ghats and cools.", "page": "141", "blocks": ["p0001-b0002"]},
    {"n": 2, "text": "Air coming down the other side stays dry.", "page": "142", "blocks": ["p0001-b0003"]}],
    chapter_terms=frozenset(studio.chapter_terms(PAGES)))


class BookLines(unittest.TestCase):
    """Navin, 20 November 2026: "video ki script jo teacher samjha raha hai usse har baat cover honi chahiye" and "tum mujhe
    batao is video se NCERT ka konsa text clear hota hai". The film is checked line by line against the book."""

    def test_book_lines_are_whole_sentences_with_their_printed_page(self):
        lines = studio.book_lines(PAGES, WANTED)
        texts = [line["text"] for line in lines]
        self.assertEqual(texts[0], "Figure 11.7 ATP synthesis through chemiosmosis")          # a caption is its own line
        self.assertIn("Why are we so interested in the proton gradient?", texts)
        self.assertFalse([t for t in texts if t.startswith("Hence")], texts)                # mostly another question's line
        joined = [t for t in texts if t.startswith("The gradient is broken down")][0]       # across lines and a page break
        self.assertTrue(joined.endswith("through the channel of the CF0 of the ATP synthase."), joined)  # subscript put back
        self.assertIn("The ATP is used to fix CO2 in the stroma.", texts)
        self.assertNotIn("2024-25", " ".join(texts))
        self.assertNotIn("BIOLOGY", " ".join(texts))
        self.assertEqual([line["page"] for line in lines][:2], ["141", "141"])
        self.assertEqual(lines[-1]["page"], "142")
        self.assertEqual([line["n"] for line in lines], list(range(1, len(lines) + 1)))
        self.assertEqual(studio.book_lines(PAGES, []), [])

    def test_a_follow_up_line_without_key_words_is_taught_by_the_sentence_that_lists_it(self):
        # Photosynthesis q08 (batch 2, 21 November 2026): "If yes, which one?" has no key word, so asking for its key
        # words could never be met; the film spent all 5 rounds on it
        self.assertEqual(studio_film._content_words("If yes, which one?"), set())
        self.assertEqual(studio_film._content_words("Let us see how this happens."), set())       # the book talking
        self.assertEqual(studio_film._content_words("You are definitely right."), set())          # to the reader
        question = dict(BOOK_Q, book_lines=[dict(BOOK_Q["book_lines"][0]), {"n": 2, "text": "If yes, which one?", "page": "1"}])
        self.assertEqual(studio_film.book_problems(taught_film([[], [1], [], [2]]), question), [])
        self.assertIn("book line B2 is not taught", " | ".join(studio_film.book_problems(taught_film([[], [1], [], []]), question)))

    def test_terms_the_chapter_never_uses(self):
        known = studio.chapter_terms(PAGES)
        self.assertEqual(studio.unknown_terms("G3P banta hai; CO2, H2O, CF0 aur ATP chapter ke hain, Pi bhi", known), ["G3P"])
        self.assertEqual(studio.unknown_terms("Ab RuBP aur G3P", known), ["RuBP", "G3P"])

    def test_every_book_line_is_taught_with_its_words(self):
        good = taught_film([[], [1], [], [2]])
        self.assertEqual(studio_film.problems(good, BOOK_Q), [])
        found = " | ".join(studio_film.problems(taught_film([[], [1], [], []]), BOOK_Q))
        self.assertIn("book line B2 is not taught: Air coming down the other side stays dry.", found)
        found = " | ".join(studio_film.problems(taught_film([[2], [1], [], [9]]), BOOK_Q))
        self.assertIn("none of its key words is spoken", found)                             # B2 claimed by the opening question
        self.assertIn("teaches B9, but the book lines are B1 to B2", found)
        bad = taught_film([[], [1], [], [2]])
        del bad["shots"][0]["sentences"][0]["teaches"]
        self.assertIn("teaches is missing", " ".join(studio_film.problems(bad, BOOK_Q)))
        rich = taught_film([[], [1], [], [2]], beyond=("a", "b", "c", "d"))                  # beyond the book: welcome
        self.assertEqual(studio_film.problems(rich, BOOK_Q), [])
        flat = taught_film([[], [1], [], [2]])
        for s in flat["shots"][1]["sentences"]:
            s["part"] = "concept"
        found = " | ".join(studio_film.problems(flat, BOOK_Q))
        self.assertIn("no sentence is a prerequisite", found)
        self.assertIn("no sentence is a use", found)
        self.assertEqual(studio_film.problems(film(), QUESTION), [])                         # without book lines: as before

    def test_words_are_free_and_only_listed(self):
        """Navin, 20 November 2026: a strict rule against words outside the book would weaken "humara padhana kaise hai";
        a name the chapter never uses is not sent back, only listed on the review page."""
        free = taught_film([[], [1], [], [2]])
        free["shots"][0]["sentences"][1]["roman"] = "Hawa Ghats par chadhkar thandi hoti hai (cools), jaise G3P ki kahani, aur barasti hai."
        free["shots"][1]["sentences"][1]["moves"] = [dict(CLOUDS, what="G3P", label="", loop=False)]
        self.assertEqual(studio_film.problems(free, BOOK_Q), [])
        html = studio_film.coverage_page(free, BOOK_Q)
        self.assertIn("Kitab se bahar ke shabd (sirf jaankari, film inse rukti nahi): G3P", html)
        self.assertNotIn("Use the book's own names", studio_film.INSTRUCTIONS)
        self.assertIn("Words are free", studio_film.INSTRUCTIONS)

    def test_beyond_notes_are_in_the_course_language(self):
        """The Q14 remake (20 November 2026) wrote its beyond notes in English; Navin reads the review page in Hinglish."""
        system = studio_film.messages(BOOK_Q, course="Class 9", language="Hinglish")[0]["content"]
        self.assertIn("naming what it adds beyond the book, written in\n  Hinglish in Roman script", system)

    def test_one_thing_at_a_time_and_a_wheel_explained_station_by_station(self):
        busy = living_film()
        busy["shots"][1]["sentences"][1]["cycles"] = [dict(CALVIN_BUSY)]
        found = " | ".join(studio_film.problems(busy, QUESTION))
        self.assertIn("8 different molecules on screen at once", found)
        rushed = living_film()
        rushed["shots"][1]["sentences"] = rushed["shots"][1]["sentences"][:2]   # the whole wheel told in one sentence (Q14)
        found = " | ".join(studio_film.problems(rushed, QUESTION))
        self.assertIn("a wheel with 3 stations turns for only 0 sentence(s) after the one that starts it", found)
        vague = living_film()                       # Q14's ending: the stations made 3-PGA, G3P and RuBP, one sentence said it all
        vague["shots"][1]["sentences"][4]["roman"] = "Cycle aise hi chalta rehta hai."
        vague["shots"][1]["sentences"][4]["voice"] = "साइकिल ऐसे ही चलता रहता है।"
        found = " | ".join(studio_film.problems(vague, QUESTION))
        self.assertIn("station 'regeneration' is not explained in a sentence of its own", found)

    def test_maker_gets_numbered_lines_and_the_other_films(self):
        q = dict(BOOK_Q, other_questions=["q02: Baadal kaise bante hain?"])
        user = studio_film.messages(q, course="Class 9", language="Hinglish")[1]["content"]
        self.assertIn("B1 (page 141): The wind climbs the Ghats and cools.", user)
        self.assertIn("Taught in this course's other films (a bridge at most here):\n- q02: Baadal kaise bante hain?", user)
        for rule in ("EVERY BOOK LINE IS TAUGHT", "GO BEYOND THE BOOK WHEREVER IT MAKES THE CONCEPT CLEARER",
                     "THE WHOLE PICTURE", "CONTEXT AND BASICS", "ONE THING AT A TIME", "never invented blobs"):
            self.assertIn(rule, studio_film.INSTRUCTIONS)
        props = studio_film.SCHEMA["properties"]["shots"]["items"]["properties"]["sentences"]["items"]["properties"]
        self.assertIn("teaches", props)
        self.assertIn("beyond", props)
        self.assertEqual(props["part"]["enum"], ["hook", "prerequisite", "concept", "use", "recap"])

    def test_coverage_page_for_navin(self):
        f = taught_film([[], [1], [], []], beyond=("", "", "", "ghaat ki oonchai kitab mein nahi <b>"))
        html = studio_film.coverage_page(f, BOOK_Q, chapter="Monsoon")
        for text in ("1 / 2</b> NCERT lines film mein padhayi gayi", "NCERT page 141, 142", "learner ko nahi dikhta",
                     "✗ nahi padhaya", "Hawa Ghats par chadhkar thandi hoti hai", "ghaat ki oonchai kitab mein nahi &lt;b&gt;",
                     "Film ka dhaancha: sawaal: 1 · pehle ki baat: 1 · concept: 1 · kahan kaam aata hai / asar: 1",
                     '<span class="part">kahan kaam aata hai / asar</span>'):
            self.assertIn(text, html)
        c = studio_film.coverage(f, BOOK_Q)
        self.assertEqual((c["taught"], c["total"], len(c["beyond"])), (1, 2, 1))

    def test_player_is_one_film_not_numbered_slides(self):
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for gone in ('id="dots"', "padStart", "b.textContent=(i+1)"):
            self.assertNotIn(gone, page)
        self.assertIn('id="bar"', page)
        self.assertIn("bar(si,k,playing)", page[page.index("function sentence(k)"):page.index("function speak(")])
        self.assertIn("freezeBar()", page[page.index("function stop()"):])
        self.assertIn("$('sc').textContent=s.title||''", page)


class LabelsOnThePicture(unittest.TestCase):
    """Navin's Q14 review (20 November 2026): labels sat on the wrong structures ("stroma aur lumen dono pins left ke green
    granum stack par lag gaye"). The maker writes points before the picture exists; a vision call moves them onto it."""

    def shot(self):
        f = living_film()
        s = f["shots"][1]
        s["sentences"][0]["pins"] = [{"label": "stroma", "x": 20, "y": 20}]
        s["sentences"][0]["zoom"] = {"x": 50, "y": 50, "scale": 1.6}
        return f, s

    def test_every_point_is_listed_with_what_it_is(self):
        f, s = self.shot()
        nxt = {"title": "Andar", "dive": {"x": 40, "y": 60}, "visual": {"image_prompt": "close-up of the membrane"}}
        items = studio_film.place_items(s, nxt)
        ids = {i["id"] for i in items}
        for iid in ("s0.pin0", "s0.react0.at", "s0.react0.in0", "s0.react0.out1", "s1.cycle0", "s0.zoom", "dive"):
            self.assertIn(iid, ids)
        pin = next(i for i in items if i["id"] == "s0.pin0")
        self.assertEqual((pin["what"], pin["points"]), ("label 'stroma'", [[20.0, 20.0]]))
        self.assertIn("close-up of the membrane", next(i for i in items if i["id"] == "dive")["what"])
        msgs = studio_film.place_messages(items, {"type": "image", "media_type": "image/jpeg", "data": "AAAA"})
        self.assertEqual(msgs[1]["content"][1]["type"], "image")
        self.assertNotIn('"set"', msgs[1]["content"][0]["text"])
        self.assertTrue(strict_ready(studio_film.PLACE_SCHEMA))

    def test_sound_points_are_written_back_and_bad_ones_refused(self):
        f, s = self.shot()
        nxt = {"title": "Andar", "dive": {"x": 40, "y": 60}, "visual": {"image_prompt": "x"}}
        items = studio_film.place_items(s, nxt)
        result = studio_film.apply_places(items, {"items": [
            {"id": "s0.pin0", "points": [[99, 70]], "visible": True},             # clamped to 97
            {"id": "s0.react0.at", "points": [[61, 44]], "visible": True},
            {"id": "s1.cycle0", "points": [[30, 30], [40, 40]], "visible": True},  # wrong count: refused
            {"id": "dive", "points": [[120, 50]], "visible": True},                # outside the picture: refused
            {"id": "s0.zoom", "points": [[50, 50]], "visible": False},              # unchanged but not in the picture
        ]})
        self.assertEqual(s["sentences"][0]["pins"][0], {"label": "stroma", "x": 97.0, "y": 70.0})
        self.assertEqual(s["sentences"][0]["reacts"][0]["at"], [61.0, 44.0])
        self.assertEqual((s["sentences"][1]["cycles"][0]["x"], nxt["dive"]["x"]), (55, 40))
        self.assertEqual((result["moved"], result["refused"]), (2, 2))
        self.assertEqual(result["missing"], ["camera target: the part this sentence talks about"])

    def test_a_failed_call_keeps_the_makers_points(self):
        f, s = self.shot()
        class Broken:
            def chat(self, **kw):
                raise RuntimeError("plan limit")
        result = studio_film.place(Broken(), "m", s, None, {"type": "image", "media_type": "image/jpeg", "data": "AAAA"})
        self.assertEqual(s["sentences"][0]["pins"][0]["x"], 20)
        self.assertIn("plan limit", result["error"])

    def test_the_stage_places_labels_on_each_picture(self):
        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "qrun"
            run_dir.mkdir()
            (run_dir / "questions.json").write_text(json.dumps({"chapter_title": "Monsoon", "questions": [QUESTION]}), encoding="utf-8")
            args = SimpleNamespace(stage="films", source="", from_run=str(run_dir), videos="q01", out=str(Path(folder) / "out"),
                                   pages="", course="Class 9", language="Hinglish", model="", max_rounds=2)
            client = FakeClient([film(), {"items": [{"id": "s0.pin0", "points": [[62, 41]], "visible": True}]}])
            summary = vm_studio.run(args, client=client, load=None, voice_maker=lambda: (FakeVoice(), None))
            self.assertEqual(summary["status"], "ok", summary)
            made = json.loads((Path(folder) / "out" / "films" / "q01.json").read_text(encoding="utf-8"))
            self.assertEqual(made["film"]["shots"][0]["sentences"][0]["pins"][0]["x"], 62.0)
            self.assertEqual(made["placement"]["s1"]["moved"], 1)
            self.assertEqual(summary["films"][0]["points_moved"], 1)
            self.assertIn('"x": 62.0', (Path(folder) / "out" / "films" / "q01.html").read_text(encoding="utf-8").replace('"x":62.0', '"x": 62.0'))

    def test_pictures_carry_no_arrows_and_scale_grows(self):
        for suffix in (studio_film.IMAGE_SUFFIX, studio_film.CUTAWAY_SUFFIX):
            self.assertIn("no arrows or symbols", suffix)
        self.assertIn("no loose molecules", studio_film.CUTAWAY_SUFFIX)
        for rule in ("SCALE GROWS STEP BY", "drawn closed", "a leak is a clear gap", "shown\n  happening, moving"):
            self.assertIn(rule, studio_film.INSTRUCTIONS)


class FilmStage(unittest.TestCase):
    def test_films_stage_makes_a_phone_film(self):
        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "qrun"
            run_dir.mkdir()
            (run_dir / "questions.json").write_text(json.dumps({"chapter_title": "Monsoon", "questions": [QUESTION]}), encoding="utf-8")
            args = SimpleNamespace(stage="films", source="", from_run=str(run_dir), videos="q01", out=str(Path(folder) / "out"),
                                   pages="", course="Class 9", language="Hinglish", model="", max_rounds=2)
            client = FakeClient([film()])
            summary = vm_studio.run(args, client=client, load=None, voice_maker=lambda: (FakeVoice(), None))
            out = Path(folder) / "out"
            self.assertEqual(summary["status"], "ok", summary)
            self.assertEqual(client.images, 1)
            page = (out / "films" / "q01.html").read_text(encoding="utf-8")
            self.assertNotIn("/*__FILM__*/null", page)
            self.assertIn("data:image/webp;base64,", page)
            self.assertIn("घाट की दीवार", (out / "films" / "q01.json").read_text(encoding="utf-8"))
            self.assertIn("const BIEVoice=", page)                     # the voice that plays (data: URI, then Web Audio)
            self.assertNotIn("/*__VOICE__*/", page)
            self.assertTrue((out / "FILMS.md").exists())

    def test_films_stage_writes_the_ncert_page(self):
        lines = [{"text": "The wind climbs the Ghats and cools.", "box": LINE(0.2)},
                 {"text": "Air coming down the other side stays dry.", "box": LINE(0.22)}]
        pages = [page(1, [("HEAD 7", (0.1, 0.1, 0.9, 0.11))] + [(x["text"], x["box"]) for x in lines])]
        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "qrun"
            run_dir.mkdir()
            other = dict(QUESTION, id="q02", question="Baadal kaise bante hain?")
            (run_dir / "questions.json").write_text(json.dumps({"chapter_title": "Monsoon", "questions": [QUESTION, other]}),
                                                    encoding="utf-8")
            args = SimpleNamespace(stage="films", source="book.pdf", from_run=str(run_dir), videos="q01",
                                   out=str(Path(folder) / "out"), pages="", course="Class 9", language="Hinglish", model="",
                                   max_rounds=2)
            seen = {}

            class Client(FakeClient):
                def chat(self, *, model, messages, schema=None):
                    seen.setdefault("user", messages[1]["content"])          # the maker's call (placement comes later)
                    return super().chat(model=model, messages=messages, schema=schema)

            client = Client([taught_film([[], [1], [], [2]])])
            summary = vm_studio.run(args, client=client, load=lambda data, wanted, with_images: ("h", 1, pages),
                                    read=lambda source: b"%PDF-1.4", voice_maker=lambda: (FakeVoice(), None))
            out = Path(folder) / "out"
            self.assertEqual(summary["status"], "ok", summary)
            self.assertIn("B2 (page 7): Air coming down the other side stays dry.", seen["user"])
            self.assertIn("- q02: Baadal kaise bante hain?", seen["user"])
            self.assertIn("2 / 2</b> NCERT lines", (out / "films" / "q01-ncert.html").read_text(encoding="utf-8"))
            self.assertIn("NCERT lines 2/2", (out / "FILMS.md").read_text(encoding="utf-8"))
            self.assertEqual(len(json.loads((out / "films" / "q01.json").read_text(encoding="utf-8"))["book_lines"]), 2)

    def test_job_for_films(self):
        job = codex_vm.validate({"job": "bie.vm-job/1", "id": "studio-films-test", "section": "studio", "stage": "films",
                                 "from_run": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/x",
                                 "source": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-inputs/chapters/x.pdf",
                                 "videos": "q01,q02"})
        cmd = codex_vm.argv(job, Path("/tmp/o"), "python")
        self.assertEqual(cmd[cmd.index("--from-run") + 1], job["from_run"])
        self.assertEqual(cmd[cmd.index("--videos") + 1], "q01,q02")
        self.assertNotIn("--chapter-map", cmd)
        heading = codex_vm.validate(dict(job, id="studio-films-h", videos="h11-7-2a,h11-6-3b",
                                         chapter_map="https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/n"))
        cmd = codex_vm.argv(heading, Path("/tmp/o"), "python")       # films from a script run: the naksha run's chapter map
        self.assertEqual(cmd[cmd.index("--chapter-map") + 1], heading["chapter_map"])
        self.assertEqual(cmd[cmd.index("--videos") + 1], "h11-7-2a,h11-6-3b")
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({"job": "bie.vm-job/1", "id": "studio-films-x", "section": "studio", "stage": "films"})


if __name__ == "__main__":
    unittest.main()


def said(roman, voice, pins=()):
    return sentence(roman, voice, pins)


class TeacherVoice(unittest.TestCase):
    """Navin rewrote the Q14 script (20 November 2026): sentences a teacher would say, a question told apart from its
    answer, the respectful "aap" voice, an invitation after the opening question, and his own lines kept when he gives
    them."""

    def lines_of(self, *pairs):
        bad = film()
        bad["shots"][0]["sentences"] = [said(r, v) for r, v in pairs]
        return bad

    def test_a_question_running_into_its_answer_is_sent_back(self):
        bad = self.lines_of(("Yeh Ghat baarish kyun rokti hai? Aaiye jaante hain.", "यह घाट बारिश क्यों रोकती है? आइए जानते हैं।"),
                            ("Hawa itni thandi kyun—kyunki upar dabav kam hai.", "हवा इतनी ठंडी क्यों—क्योंकि ऊपर दबाव कम है।"))
        found = " | ".join(studio_film.teacher_problems(bad, QUESTION))
        self.assertIn("s1 sentence 2: the question runs straight into its answer", found)
        self.assertIn("s1 sentence 2: the line asks a question; in voice end the question with ?", found)

    def test_navins_way_passes(self):
        good = self.lines_of(("Yeh Ghat baarish kyun rokti hai? Aaiye jaante hain.", "यह घाट बारिश क्यों रोकती है? आइए जानते हैं।"),
                             ("Par pehle, hawa itni thandi kyun? Iski wajah jaan lete hain: aisa isliye hai kyunki upar dabav kam hai.",
                              "पर पहले, हवा इतनी ठंडी क्यों? इसकी वजह जान लेते हैं: ऐसा इसलिए है क्योंकि ऊपर दबाव कम है।"),
                             ("Ek sawaal ab bhi banta hai ki baadal kahan jaate hain—iska seedha sa jawab hai pahaad ke paar.",
                              "एक सवाल अब भी बनता है कि बादल कहाँ जाते हैं? इसका सीधा सा जवाब है पहाड़ के पार।"))
        self.assertEqual(studio_film.teacher_problems(good, QUESTION), [])

    def test_orders_are_sent_back_and_the_aap_voice_passes(self):
        bad = self.lines_of(("Yeh Ghat baarish kyun rokti hai? Aaiye jaante hain.", "यह घाट बारिश क्यों रोकती है? आइए जानते हैं।"),
                            ("Pehle jagah pehchaan lo, phir yahan dekho.", "पहले जगह पहचान लो, फिर यहाँ देखो।"))
        found = " | ".join(studio_film.teacher_problems(bad, QUESTION))
        self.assertIn("'pehchaan lo' orders the learner", found)
        good = self.lines_of(("Yeh Ghat baarish kyun rokti hai? Aaiye jaante hain.", "यह घाट बारिश क्यों रोकती है? आइए जानते हैं।"),
                             ("Aaiye pehle jagah pehchaan lete hain, phir yahan dekhiye.", "आइए पहले जगह पहचान लेते हैं, फिर यहाँ देखिए।"))
        self.assertEqual(studio_film.teacher_problems(good, QUESTION), [])

    def test_the_opening_question_invites(self):
        bad = self.lines_of(("Yeh Ghat baarish kyun rokti hai?", "यह घाट बारिश क्यों रोकती है?"),
                            ("Hawa yahan chadhti hai.", "हवा यहाँ चढ़ती है।"))
        self.assertIn('invite the learner ("Aaiye jaante hain.")', " ".join(studio_film.teacher_problems(bad, QUESTION)))

    def test_the_teachers_own_lines_are_kept_word_for_word(self):
        lines = [{"roman": "Yeh Ghat ki deewar baarish kyun rokti hai? aayiye jaante hai"},
                 {"roman": "Hawa yahan chadhkar thandi hoti hai aur barasti hai.", "note": "yahan baadal ki misaal do"},
                 {"roman": "Doosri taraf hawa sookhi utarti hai."}, {"roman": "Isliye Pune sookha rehta hai."}]
        q = dict(QUESTION, teacher_lines=lines, earlier_film=film())
        made = film()
        made["shots"][0]["sentences"][0]["roman"] = "Yeh Ghat ki deewar baarish kyun rokti hai? Aaiye jaante hain."
        rest = [s for shot in made["shots"] for s in shot["sentences"]][2:]
        self.assertEqual(len(rest), 2)
        rest[0]["roman"], rest[1]["roman"] = lines[2]["roman"], lines[3]["roman"]
        self.assertEqual([p for p in studio_film.teacher_problems(made, q) if "teacher" in p], [])
        rest[1]["roman"] = "Aur baarish ka paani nadi mein jaata hai, jahan se khet seenche jaate hain."
        self.assertIn("is not the teacher's line L4", " ".join(studio_film.teacher_problems(made, q)))
        made["shots"][1]["sentences"].pop()
        self.assertIn("the film has 3 sentences and the teacher's script 4 lines", " ".join(studio_film.teacher_problems(made, q)))
        user = studio_film.messages(q, course="Class 9", language="Hinglish")[1]["content"]
        self.assertIn("THE TEACHER'S SCRIPT", user)
        self.assertIn("L2: Hawa yahan chadhkar thandi hoti hai aur barasti hai.\n    NOTE: yahan baadal ki misaal do", user)
        self.assertIn('"title": "Ghat aur baarish"', user)               # the earlier film rides along
        self.assertNotIn("THE TEACHER'S SCRIPT", studio_film.messages(QUESTION, course="Class 9", language="Hinglish")[1]["content"])

    def test_the_teachers_lines_skip_style_but_not_the_voice_question_mark(self):
        lines = [{"roman": "Yeh Ghat ki deewar baarish kyun rokti hai? Aaiye jaante hain."},
                 {"roman": "Hawa thandi kyun—kyunki upar dabav kam hai."}, {"roman": "Doosri taraf hawa sookhi utarti hai."},
                 {"roman": "Isliye Pune sookha rehta hai, dekho."}]
        made = film()
        flat = [s for shot in made["shots"] for s in shot["sentences"]]
        for s, line in zip(flat, lines):
            s["roman"] = line["roman"]
        flat[1]["voice"] = "हवा ठंडी क्यों—क्योंकि ऊपर दबाव कम है।"
        found = " | ".join(studio_film.teacher_problems(made, dict(QUESTION, teacher_lines=lines)))
        self.assertNotIn("runs straight into", found)
        self.assertNotIn("orders the learner", found)
        self.assertIn("s1 sentence 2: the line asks a question; in voice end the question with ?", found)

    def test_a_voiced_line_carries_its_gap_and_a_sign_the_voice_cannot_say_is_caught(self):
        from bie.brain import studio_voice
        audio = {("s1", 0): {"uri": "data:audio/mpeg;base64,AA", "dur": 3.0}, ("s1", 1): {"uri": "data:audio/mpeg;base64,AA", "dur": 4.0},
                 ("s2", 0): {"uri": "data:audio/mpeg;base64,AA", "dur": 3.0}}
        data = studio_film.player_data(film(), images={}, audio=audio, chapter="Monsoon", question=QUESTION)
        said = [t for shot in data["shots"] for t in shot["sentences"]]
        self.assertEqual(said[0]["after"], studio_voice.SENTENCE_PAUSE)        # "...kyun rokti hai? Aaiye jaante hain."
        self.assertEqual(said[1]["after"], studio_voice.SENTENCE_PAUSE)        # before s2, which opens by a dive (1.6 s)
        self.assertEqual(said[2]["after"], studio_voice.SENTENCE_PAUSE)
        self.assertNotIn("after", said[3])                                     # not voiced: timed by its text
        template = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn("t.after!=null?t.after*1000:450", template)
        made = film()
        made["shots"][0]["sentences"][1]["voice"] = "हवा 3 ATP/2 NADPH के हिसाब से चढ़ती है।"
        found = " | ".join(studio_film.teacher_problems(made, QUESTION))
        self.assertIn("s1 sentence 2: the voice cannot say /", found)

    def test_the_voice_speaks_a_question_on_its_own_with_a_pause(self):
        from bie.brain import studio_voice
        self.assertEqual(studio_voice.parts("बंद मेम्ब्रेन क्यों चाहिए? इसका सीधा सा जवाब है जमाव।"),
                         [("बंद मेम्ब्रेन क्यों चाहिए?", studio_voice.QUESTION_PAUSE), ("इसका सीधा सा जवाब है जमाव।", 0.0)])
        self.assertEqual(studio_voice.parts("सीधी बात।"), [("सीधी बात।", 0.0)])
        self.assertGreater(studio_voice.QUESTION_PAUSE, 0.2)

    def test_the_stage_reads_the_teachers_script(self):
        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "qrun"
            (run_dir / "teacher").mkdir(parents=True)
            (run_dir / "questions.json").write_text(json.dumps({"chapter_title": "Monsoon", "questions": [QUESTION]}), encoding="utf-8")
            lines = [{"roman": s["roman"]} for shot in film()["shots"] for s in shot["sentences"]]
            lines[1]["note"] = "baadal ki misaal do"
            (run_dir / "teacher" / "q01.json").write_text(json.dumps({"lines": lines, "film": film()}), encoding="utf-8")
            args = SimpleNamespace(stage="films", source="", from_run=str(run_dir), videos="q01", out=str(Path(folder) / "out"),
                                   pages="", course="Class 9", language="Hinglish", model="", max_rounds=2)
            seen = {}

            class Client(FakeClient):
                def chat(self, *, model, messages, schema=None):
                    seen.setdefault("user", messages[1]["content"])
                    return super().chat(model=model, messages=messages, schema=schema)

            summary = vm_studio.run(args, client=Client([film()]), load=None, voice_maker=lambda: (FakeVoice(), None))
            self.assertEqual(summary["status"], "ok", summary)
            self.assertIn("NOTE: baadal ki misaal do", seen["user"])
            self.assertEqual(summary["films"][0]["teacher_lines"], 4)
            self.assertIn("teacher ki 4 lines", (Path(folder) / "out" / "FILMS.md").read_text(encoding="utf-8"))


class TeacherStudyDrawing(unittest.TestCase):
    """The teacher study (22 November 2026; Navin's yes to F1, F2, F3, judged on a BIE video): a process built step by step
    on one picture, amounts counted with beads, an analogy on its own everyday picture, and films cut from the script."""

    def stepped(self):
        made = film()
        made["shots"][0]["sentences"] += [sentence("Phir hawa thandi hoti hai aur baadal bante hain.", "फिर हवा ठंडी होती है और बादल बनते हैं।"),
                                          sentence("Aakhir mein baadal Ghat par baraste hain.", "आख़िर में बादल घाट पर बरसते हैं।")]
        for n, line in enumerate(made["shots"][0]["sentences"][1:], 1):
            line["step"] = n
        return made

    def test_a_process_is_numbered_in_order_on_one_picture(self):
        made = self.stepped()
        self.assertTrue(studio_film.stepped_shot(made["shots"][0]))
        self.assertEqual(studio_film.teaching_problems(made, QUESTION), [])
        made["shots"][0]["sentences"][2]["step"] = 3
        found = " | ".join(studio_film.teaching_problems(made, QUESTION))
        self.assertIn("s1 sentence 3: step 3 comes where step 2 is due", found)
        made = self.stepped()
        bare = made["shots"][0]["sentences"][2]
        for key in ("arrows", "pins", "moves", "grows", "fuses", "focus"):
            bare[key] = []
        self.assertIn("s1 sentence 3: step 2 adds nothing to the picture", " | ".join(studio_film.teaching_problems(made, QUESTION)))

    def test_a_process_question_needs_its_steps_and_a_stepped_shot_may_be_longer(self):
        many = dict(QUESTION, points=[dict(QUESTION["points"][0]) for _ in range(3)])
        self.assertIn("the question has 3 process points; tell the process on one picture",
                      " | ".join(studio_film.teaching_problems(film(), many)))
        made = self.stepped()
        self.assertEqual([p for p in studio_film.teaching_problems(made, many) if "process points" in p], [])
        extra = [sentence(f"Yeh kadam {n} hai, jahan hawa aage badhti hai.", f"यह कदम {n} है, जहाँ हवा आगे बढ़ती है।") for n in range(4, 8)]
        for n, line in enumerate(extra, 4):
            line["step"] = n
        made["shots"][0]["sentences"] += extra
        found = " | ".join(studio_film.problems(made, QUESTION))
        self.assertNotIn("sentences; write 2 to", found)                   # 8 sentences, allowed on a stepped shot
        plain = film()
        plain["shots"][0]["sentences"] += [dict(x, step=0) for x in extra + extra[:1]]
        self.assertIn("s1: 7 sentences; write 2 to 6", " | ".join(studio_film.problems(plain, QUESTION)))

    def test_a_count_is_seen_and_keeps_its_atoms(self):
        made = film()
        line = made["shots"][1]["sentences"][1]
        line["roman"] = "Paanch carbon aur ek naya carbon: five plus one equals three plus three."
        self.assertIn("s2 sentence 2: the sentence counts (five plus one equals)", " | ".join(studio_film.teaching_problems(made, QUESTION)))
        line["count"] = {"x": 50, "y": 86, "groups": [{"n": 5, "label": "RuBP", "colour": "green"}, {"n": 1, "label": "CO2", "colour": "red"}],
                         "then": [{"n": 3, "label": "PGA", "colour": "green"}, {"n": 2, "label": "PGA", "colour": "green"}]}
        self.assertIn("the count has 6 beads before = and 5 after", " | ".join(studio_film.teaching_problems(made, QUESTION)))
        line["count"]["then"][1]["n"] = 3
        self.assertEqual(studio_film.teaching_problems(made, QUESTION), [])
        data = studio_film.player_data(made, images={}, audio={}, chapter="", question=QUESTION)
        self.assertEqual(data["shots"][1]["sentences"][1]["count"]["groups"][1]["n"], 1)
        self.assertEqual(data["shots"][0]["sentences"][0]["step"], 0)
        template = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for part in ("function quiet()", "function stepMark(t)", "function countAdd(c)", ".ar.old", ".beads"):
            self.assertIn(part, template)

    def test_an_analogy_has_its_own_picture_and_cuts_out_and_back(self):
        made = film()
        aside = {"id": "a1", "title": "Baandh", "key": "Baandh paani rokta hai, jaise Ghat hawa", "covers": [], "aside": True,
                 "visual": {"type": "photo", "image_prompt": "Photorealistic wide view of a concrete dam holding back a deep "
                            "blue reservoir in the monsoon, water spilling through one open gate", "svg": ""},
                 "dive": {"x": -1, "y": -1},
                 "sentences": [sentence("Ghat ko ek baandh samajhiye jo hawa rokta hai.", "घाट को एक बाँध समझिए जो हवा रोकता है।", ["baandh = Ghat"], moves=[CLOUDS]),
                               sentence("Jaise baandh paani rokta hai, waise Ghat hawa ko rokta hai.", "जैसे बाँध पानी रोकता है, वैसे घाट हवा को रोकता है।")]}
        made["shots"].insert(1, aside)
        made["shots"][2]["dive"] = {"x": -1, "y": -1}
        found = " | ".join(studio_film.problems(made, QUESTION))
        self.assertNotIn("shots cut instead of diving", found)
        self.assertEqual(studio_film.teaching_problems(made, QUESTION), [])
        made["shots"][1]["sentences"][0]["pins"] = [{"label": "baandh", "x": 40, "y": 30}]
        made["shots"][2]["dive"] = {"x": 50, "y": 40}
        found = " | ".join(studio_film.teaching_problems(made, QUESTION))
        self.assertIn("a1: the aside maps the analogy in a pin", found)
        self.assertIn("s2: after an aside the film cuts back to its world", found)

    def test_answers_do_not_all_open_alike(self):
        # the final script round (22 Nov 2026): "Dekho," opened nearly every answer; Navin, 23 Nov: "Tum wali chalegi",
        # the voice stays, only the openers vary
        def asked(opener):
            return sentence(f"Yeh hawa kyun ruk jaati hai? {opener} Ghat use upar dhakel deta hai, aur woh thandi hoti hai.",
                            "यह हवा क्यों रुक जाती है? घाट उसे ऊपर धकेल देता है, और वह ठंडी होती है।")
        made = film()
        made["shots"][0]["sentences"] += [asked("Dekho,") for _ in range(3)]
        made["shots"][1]["sentences"] += [asked("Dekho,"), asked("Iska seedha sa jawab hai,")]
        found = " | ".join(studio_film.teaching_problems(made, QUESTION))
        self.assertIn("4 of the film's 6 answers open with \"Dekho\"; open some with another teacher's opener", found)
        made["shots"][0]["sentences"][-1] = asked("Aisa isliye hai kyunki")
        self.assertEqual(studio_film.teaching_problems(made, QUESTION), [])                 # 3 of 6: not more than half
        self.assertEqual(studio_film.answer_openers(["Kyun?", "Kaise?", "Dekho, aisa hai.", "Ruko.", "Iska jawab hai."]),
                         ["dekho"])                                               # a question after a question is no answer
        script = dict(QUESTION, script_lines=True, teacher_lines=[{"roman": "x"}])
        navin = dict(QUESTION, teacher_lines=[{"roman": "x"}])
        made["shots"][0]["sentences"][-1] = asked("Dekho,")
        self.assertTrue(any("answers open with" in p for p in studio_film.teaching_problems(made, script)))
        self.assertFalse(any("answers open with" in p for p in studio_film.teaching_problems(made, navin)))  # his own lines
        self.assertIn("so that no opener starts more than half the answers", studio_film._teacher_part(
            dict(QUESTION, script_lines=True, teacher_lines=[{"roman": "Dekho, aisa hai.", "note": "explain"}])))

    def test_the_script_is_cut_into_heading_films(self):
        chapter = {"items": {"i1": {"content": "Hawa chadhti hai", "content_type": "process", "block_ids": ["b1"]},
                             "i2": {"content": "Vrishti chhaya", "content_type": "cause_effect", "block_ids": ["b2"]}}}
        says = [f"Yeh line {n} hai jo hawa ke baare mein baat karti hai." for n in range(60)]
        script = {"chapter_title": "Monsoon", "parts": [
            {"section": "1.2", "title": "Ghat", "bridge": "Ab dekhte hain doosri taraf kya hota hai.",
             "points": [{"id": f"1.2-k{n}", "kind": "analogy" if n == 1 else "explain", "teaches": ["i1" if n < 3 else "i2"],
                         "says": says[n * 10:(n + 1) * 10], "screen": f"screen {n}"} for n in range(6)]}]}
        naksha = {"A": {"films": [{"id": "a1", "section": "1.2", "question": "Ghat par baarish kyun hoti hai?", "teaches": ["i1"]},
                                  {"id": "a2", "section": "1.2", "question": "Doosri taraf sookha kyun?", "teaches": ["i2"]}]}}
        plan = studio_script.film_questions(script, chapter, naksha)
        self.assertEqual([q["id"] for q in plan["questions"]], ["h1-2a", "h1-2b"])
        first, second = plan["questions"]
        self.assertEqual(first["teacher_lines"][0], {"roman": "Ghat par baarish kyun hoti hai?", "note": "the film's opening question",
                                                     "kind": "question", "point": ""})
        self.assertEqual(second["question"], "Doosri taraf sookha kyun?")
        self.assertEqual(first["teacher_lines"][1]["note"], "explain · screen: screen 0")
        self.assertEqual(second["teacher_lines"][-1]["roman"], "Ab dekhte hain doosri taraf kya hota hai.")
        self.assertNotIn("Ab dekhte hain", first["teacher_lines"][-1]["roman"])
        self.assertTrue(first["script_lines"] and first["naksha"] is True)
        self.assertEqual(len(first["teacher_lines"]) - 1 + len(second["teacher_lines"]) - 2, 60)
        self.assertEqual([q["id"] for q in studio_script.film_questions(script, chapter, naksha, ["h1-2b"])["questions"]], ["h1-2b"])
        self.assertEqual(len(studio_script.film_questions(script, chapter, naksha, ["1.2"])["questions"]), 2)
        self.assertIn("THE CHAPTER'S SCRIPT", studio_film.messages(first, course="Class 9", language="Hinglish")[1]["content"])
        # an analogy line of the script is said on an aside shot
        made = film()
        lines = [{"roman": x["roman"], "kind": "analogy" if k == 1 else "explain", "point": "1.2-k1" if k == 1 else "1.2-k0"}
                 for k, x in enumerate(s for shot in made["shots"] for s in shot["sentences"])]
        q = dict(QUESTION, teacher_lines=lines, script_lines=True)
        self.assertIn("the script's analogy 1.2-k1 is not on its own picture", " | ".join(studio_film.teaching_problems(made, q)))

    def test_the_films_stage_reads_a_script_run(self):
        with tempfile.TemporaryDirectory() as folder:
            run_dir, map_dir = Path(folder) / "srun", Path(folder) / "nrun"
            run_dir.mkdir()
            map_dir.mkdir()
            lines = [s["roman"] for shot in film()["shots"] for s in shot["sentences"]]
            (run_dir / "script.json").write_text(json.dumps({"chapter_title": "Monsoon", "parts": [
                {"section": "1", "title": "Ghat", "bridge": "", "points": [
                    {"id": "1-k1", "kind": "explain", "teaches": ["i1", "i2"], "says": lines, "screen": "Ghat aur baadal"}]}]}),
                encoding="utf-8")
            (map_dir / "chapter_map.json").write_text(json.dumps({"items": {
                "i1": {"content": "Hawa chadhti hai", "content_type": "process", "block_ids": ["b1"]},
                "i2": {"content": "Vrishti chhaya", "content_type": "cause_effect", "block_ids": ["b2"]}}}), encoding="utf-8")
            args = SimpleNamespace(stage="films", source="", from_run=str(run_dir), chapter_map=str(map_dir), videos="h1",
                                   out=str(Path(folder) / "out"), pages="", course="Class 9", language="Hinglish", model="",
                                   max_rounds=1)
            seen = {}

            class Client(FakeClient):
                def chat(self, *, model, messages, schema=None):
                    seen.setdefault("user", messages[1]["content"])
                    return super().chat(model=model, messages=messages, schema=schema)

            summary = vm_studio.run(args, client=Client([film()]), load=None, voice_maker=lambda: (FakeVoice(), None))
            self.assertIn("THE CHAPTER'S SCRIPT", seen["user"])
            self.assertIn("NOTE: explain · screen: Ghat aur baadal", seen["user"])
            self.assertEqual((summary["films"][0]["qid"], summary["films"][0]["teacher_lines"]), ("h1", 5))   # the opening line is two sentences


class ReviewFindings(unittest.TestCase):
    """The review of the third Q14 film (20 November 2026): flows that stop, labels on top of each other, a structure
    changing sides between pictures, two shots of 54 seconds."""

    def test_two_pins_on_one_spot_are_sent_back(self):
        bad = film()
        line = bad["shots"][0]["sentences"][1]
        line["roman"] = "Thylakoid ke andar lumen hai aur hawa barasti hai."
        line["pins"] = [{"label": "thylakoid", "x": 64, "y": 58}, {"label": "lumen", "x": 65, "y": 61}]
        found = " | ".join(studio_film.problems(bad, QUESTION))
        self.assertIn("labels 'thylakoid' and 'lumen' are 3% apart", found)
        line["pins"][1].update(x=72, y=70)
        self.assertNotIn("apart, on top of each other", " | ".join(studio_film.problems(bad, QUESTION)))

    def test_a_structure_keeps_its_side_from_picture_to_picture(self):
        def shot(sid, pump, synthase):
            return {"id": sid, "sentences": [{"pins": [{"label": "proton pump", "x": pump, "y": 50},
                                                       {"label": "ATP synthase", "x": synthase, "y": 40}]}]}
        flipped = {"shots": [shot("s4", 30, 72), shot("s5", 50, 50), shot("s6", 89, 25)]}
        found = studio_film.layout_problems(flipped)
        self.assertEqual(len(found), 1)
        self.assertIn("s6: 'proton pump' is left of 'atp synthase' in s4 but right of it here", found[0])
        self.assertEqual(studio_film.layout_problems({"shots": [shot("s4", 30, 72), shot("s6", 20, 80)]}), [])

    def test_a_long_shot_is_split(self):
        bad = film()
        bad["shots"][0]["sentences"][1]["roman"] = "Hawa yahan chadhkar thandi hoti hai aur barasti hai. " * 12
        self.assertIn("s1: ", " ".join(p for p in studio_film.problems(bad, QUESTION) if "characters of narration" in p))

    def test_a_short_flow_keeps_flowing_while_its_sentence_is_spoken(self):
        short = {"what": "dot", "points": [[0, 0], [9, 9]], "count": 1, "ms": 2000}
        long_trip = dict(short, ms=8000)
        looping = dict(short, loop=True)
        moved = studio_film.held([short, long_trip, looping], 10.0)
        self.assertEqual([m.get("hold") for m in moved], [True, None, None])
        self.assertNotIn("hold", short)                                  # the film itself is not changed
        made = film()
        made["shots"][0]["sentences"][1]["moves"] = [short]
        data = studio_film.player_data(made, images={}, audio={("s1", 1): {"uri": "", "dur": 9.0}}, chapter="", question=QUESTION)
        self.assertTrue(data["shots"][0]["sentences"][1]["moves"][0]["hold"])
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for hook in ("until:m.hold&&!m.loop&&until?until:0", "addMove(m,now+(m.at!=null?m.at*1000:300),now+300+(t.dur||0)*1000)", "if(!rep&&ac.until)"):
            self.assertIn(hook, page)


class TwoFilmsOf1163b(unittest.TestCase):
    """Navin on the two 11.6.3b films (23 November 2026): the first explained the mechanism better ("bolte huye screen par
    wahi step par dhyan jata hai jo ho rha hai"), its turbine was a real one, the second felt more khichdi."""

    def test_a_pin_and_a_move_start_as_their_name_is_said(self):
        roman = "Pehle pump kaam karta hai, phir H⁺ CF₀ se stroma mein lautte hain."
        self.assertIsNone(studio_film.said_at(["NADPH"], roman, 6.0))
        early, late = studio_film.said_at(["pump"], roman, 6.0), studio_film.said_at(["H+"], roman, 6.0)
        self.assertLess(early, late)
        self.assertLessEqual(studio_film.said_at(["stroma"], roman, 6.0), 6.0 - 1.5)     # room to finish in its line
        said = studio_film.word_times({"pins": [{"label": "stroma", "x": 50, "y": 20}, {"label": "lumen", "x": 50, "y": 80}],
                                       "moves": [{"what": "H+", "points": [[1, 1], [2, 2]]}]}, roman, 6.0)
        self.assertIn("at", said["pins"][0])
        self.assertNotIn("at", said["pins"][1])                  # never said: the player starts it with the line
        self.assertIn("at", said["moves"][0])
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn("addLabel(p.t,p.x,p.y,'pin new',now+(p.at!=null?p.at*1000:0))", page)
        self.assertIn("born=now+(m.at!=null?m.at*1000:300)", page[page.index("function handOff("):])

    def test_the_camera_stays_unless_the_line_brings_something_new(self):
        z = lambda x, y, s: {"x": x, "y": y, "scale": s}
        lines = [{"roman": "Dekho CF0.", "zoom": z(60, 60, 1.6), "pins": [{"label": "CF0"}]},
                 {"roman": "Kyun?", "zoom": z(30, 30, 1.4), "pins": [{"label": "x"}]},              # a question: still
                 {"roman": "Iska jawab aage.", "zoom": z(20, 20, 2.0)},                              # nothing new: still
                 {"roman": "Ab H+ chalta hai.", "zoom": z(62, 61, 1.65), "moves": [{"what": "H+"}]},  # a tiny shift: still
                 {"roman": "Ab stroma.", "zoom": z(40, 20, 1.2), "pins": [{"label": "stroma"}]}]
        got = [(c["x"], c["y"], c["scale"]) for c in studio_film.steady_camera(lines)]
        self.assertEqual(got, [(60, 60, 1.6)] * 4 + [(40, 20, 1.2)])
        data = studio_film.player_data(film(), images={}, audio={}, chapter="", question=QUESTION)
        self.assertTrue(all(set(s["zoom"]) == {"x", "y", "scale"} for s in data["shots"][0]["sentences"]))

    def test_a_picture_draws_no_crowd_and_a_photo_no_model(self):
        made = film()
        made["shots"][0]["visual"]["image_prompt"] = "a thylakoid with visibly higher proton population space below"
        self.assertIn("crowd of molecules", " ".join(studio_film.crowd_problems(made)))
        made["shots"][0]["visual"]["image_prompt"] = "a thylakoid; leave the lumen clear for the protons BIE moves"
        self.assertEqual(studio_film.crowd_problems(made), [])
        dam = {"id": "s6", "visual": {"type": "photo", "image_prompt": "16:9 photoreal glossy hydroelectric teaching model"}}
        self.assertIn("not a model", " ".join(studio_film.photo_problems({"shots": [dam]})))
        self.assertNotIn("glossy", studio_film.image_prompt(dam, "Glossy scientific realism, warm light"))
        real = {"id": "s7", "visual": {"type": "photo", "image_prompt": "a real dam; small scientific model inset upper right"}}
        self.assertEqual(studio_film.photo_problems({"shots": [real]}), [])
        cut = {"id": "s2", "visual": {"type": "cutaway", "image_prompt": "glossy ATP synthase in a membrane"}}
        self.assertNotIn("glossy ATP", studio_film.image_prompt(cut, "", "mixed"))      # another look is not also glossy
        self.assertIn("glossy ATP", studio_film.image_prompt(cut, "", "glossy"))

    def test_the_rest_dims_when_the_camera_closes_in(self):
        """Navin, 23 November 2026: "zoom sahi jagah, roshni sahi jagah"; the ATP synthase demo he passed dimmed all but
        the part in its close-up. The light is centred on the zoom point and grows with the zoom."""
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn('<div class="spot" id="spot"></div>', page)
        cam = page[page.index("function camStep("):page.index("function toScreen(")]
        self.assertIn("spotlight();", cam)
        spot = page[page.index("function spotlight("):]
        self.assertIn("(cam.s-1.15)/.35", spot)                                  # no dimming on a wide view
        self.assertIn("'+cam.ox.toFixed(1)+'% '+cam.oy.toFixed(1)+'%", spot)    # centred on the zoom point

    def test_a_picture_leaves_room_for_the_checklist_and_never_draws_it(self):
        made = film()
        made["shots"][0]["visual"]["image_prompt"] = "a membrane; open space for an upper-center four-item checklist"
        self.assertIn("four-item", " ".join(studio_film.overlay_problems(made)))
        made["shots"][0]["visual"]["image_prompt"] = "a membrane; the upper centre is left clear"
        self.assertEqual(studio_film.overlay_problems(made), [])
        text = studio_film.messages(QUESTION, course="Geography", language="Hinglish")[0]["content"]
        self.assertIn("checklist, a panel or", text)


class LookWordsAndLabelGaps(unittest.TestCase):
    """The two Q14 remakes of 20 November 2026: a look line with "copper left" and "central stalk" matched a cell picture's
    "upper left open" and "central vacuole", so ATP synthase was drawn on the cell again; and a move's label ended on a
    pin ("Patta" and "Dhoop" on one spot)."""

    LOOK = ("16:9 realistic journey, golden light aur teal shadows; leaf emerald, mesophyll cell translucent jade, chloroplast "
            "envelope sage green, thylakoid membrane dark green, stroma ivory-teal; proton pump copper left, ATP synthase right "
            "with amber CF0 ring, silver central stalk and violet six-lobed CF1 head facing stroma; H+ gold")

    def test_place_and_size_words_do_not_bring_a_structure_in(self):
        cell = ("Transparent cutaway of one mesophyll cell, large central vacuole, chloroplasts along the wall. Selected "
                "chloroplast right at 70,52. No molecular proteins. Leave upper left open for light.")
        grana = "Inside one chloroplast: thylakoid membrane stacks and the stroma around them, no proteins."
        membrane = "The thylakoid membrane with a proton pump at left and ATP synthase at right, stroma above."
        for prompt in (cell, grana):
            shared = studio_film.look_for(prompt, self.LOOK)
            for absent in ("ATP synthase", "proton pump", "central stalk", "CF1 head"):
                self.assertNotIn(absent, shared, (prompt[:30], shared))
        self.assertIn("mesophyll cell translucent jade", studio_film.look_for(cell, self.LOOK))
        self.assertIn("stroma ivory-teal", studio_film.look_for(grana, self.LOOK))
        shared = studio_film.look_for(membrane, self.LOOK)
        for present in ("proton pump copper left", "ATP synthase right with amber CF0 ring", "silver central stalk"):
            self.assertIn(present, shared)

    def test_a_pin_label_moves_off_a_wheels_name(self):
        # Photosynthesis q05 (batch 1, 21 November 2026): the "6 H2O" pin sat on the "Water-hisaab" wheel name for about
        # 15 seconds, because the keep-apart step skipped centre (math) labels; now they are fixed obstacles
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        place = page[page.index("function placeLabels("):page.index("// --- arrows and effects")]
        self.assertIn("fixed=labels.filter(l=>l.box.style.opacity==='1'&&l.math)", place)
        self.assertIn("[...fixed,...shown.slice(0,i)]", place)
        self.assertIn("for(let pass=0;pass<4;pass++)", place)

    def test_a_move_label_ending_on_a_pin_is_sent_back(self):
        bad = film()
        line = bad["shots"][0]["sentences"][1]
        line["roman"] = "Yeh patta dhoop le raha hai aur hawa barasti hai."
        line["pins"] = [{"label": "Patta", "x": 60, "y": 50}]
        line["moves"] = [dict(CLOUDS, label="Dhoop", points=[[10, 10], [60, 50]])]
        self.assertIn("labels 'Patta' and 'Dhoop' are 0% apart", " ".join(studio_film.problems(bad, QUESTION)))
        line["moves"][0]["points"] = [[10, 10], [30, 20]]
        self.assertNotIn("'Patta' and 'Dhoop'", " ".join(studio_film.problems(bad, QUESTION)))


class PictureCupboard(unittest.TestCase):
    """The almaari (Navin, 21 November 2026): the best picture of a scene is kept and used again; a new one is drawn only
    when no kept picture fits."""

    def cupboard(self, folder):
        run = Path(folder) / "run"
        (run / "films" / "img").mkdir(parents=True)
        made = film()
        made["shots"][0]["sentences"][1]["pins"] = [{"label": "Ghat", "x": 40, "y": 55}]
        (run / "films" / "q01.json").write_text(json.dumps({"film": made, "images": {"s1": "q01-s1.png"}}), encoding="utf-8")
        (run / "films" / "img" / "q01-s1.png").write_bytes(png_bytes())
        sys.path.insert(0, str(ROOT / "tools"))
        import picture_library
        return picture_library.build(Path(folder) / "qrun", [f"{run}|q01|s1|ghat-wall|mountain wall"], approved="Navin, 21 Nov 2026")

    def test_a_kept_picture_carries_what_it_shows_and_where(self):
        with tempfile.TemporaryDirectory() as folder:
            library = self.cupboard(folder)
            kept = library["pictures"][0]
            self.assertEqual((kept["id"], kept["file"], kept["scale"]), ("ghat-wall", "library/ghat-wall.png", "mountain wall"))
            self.assertIn({"label": "Ghat", "x": 40, "y": 30}, kept["places"])          # the first place a label is pinned
            self.assertTrue((Path(folder) / "qrun" / "library" / "ghat-wall.png").exists())
            self.assertEqual(vm_studio.kept_pictures(str(Path(folder) / "qrun"))[0]["id"], "ghat-wall")

    def test_the_maker_sees_the_cupboard_and_names_only_what_is_in_it(self):
        q = dict(QUESTION, library=[{"id": "ghat-wall", "type": "cutaway", "scale": "wall", "shows": "Mountain wall in rain",
                                     "places": [{"label": "Ghat", "x": 40, "y": 55}], "file": "library/ghat-wall.png"}])
        user = studio_film.messages(q, course="Class 9", language="Hinglish")[1]["content"]
        self.assertIn("THE PICTURE CUPBOARD", user)
        self.assertIn("- ghat-wall (cutaway, set -, scale: wall): Mountain wall in rain\n  labelled places: Ghat (40,55)", user)
        made = film()
        made["shots"][0]["visual"]["library"] = "ghat-wall"
        self.assertEqual(studio_film.library_problems(made, q), [])
        made["shots"][0]["visual"]["library"] = "sea-wall"
        self.assertIn("s1: no kept picture 'sea-wall'", " ".join(studio_film.library_problems(made, q)))
        self.assertNotIn("PICTURE CUPBOARD", studio_film.messages(QUESTION, course="Class 9", language="Hinglish")[1]["content"])

    def test_the_stage_uses_a_kept_picture_instead_of_drawing(self):
        with tempfile.TemporaryDirectory() as folder:
            self.cupboard(folder)
            run_dir = Path(folder) / "qrun"
            (run_dir / "questions.json").write_text(json.dumps({"chapter_title": "Monsoon", "questions": [QUESTION]}), encoding="utf-8")
            made = film()
            made["shots"][0]["visual"].update(type="cutaway", library="ghat-wall", image_prompt="Mountain wall in monsoon rain, clouds climbing the western slope, wet green forest, painterly 3D.")
            client = FakeClient([made])
            args = SimpleNamespace(stage="films", source="", from_run=str(run_dir), videos="q01", out=str(Path(folder) / "out"),
                                   pages="", course="Class 9", language="Hinglish", model="", max_rounds=2)
            summary = vm_studio.run(args, client=client, load=None, voice_maker=lambda: (FakeVoice(), None))
            self.assertEqual(summary["status"], "ok", summary)
            self.assertEqual(summary["films"][0]["kept_pictures"], 1)
            self.assertEqual(client.images, 0)                          # nothing was drawn for the kept scene
            self.assertIn("almaari se 1 tasveer", (Path(folder) / "out" / "FILMS.md").read_text(encoding="utf-8"))

    def test_a_job_names_its_own_cupboard(self):
        """Navin, 24 November 2026: the first 11.6.3b film's real dam "almari mein bhi thi", yet the remake drew a new one,
        because a cupboard was read only beside the script run. A job now names its cupboard (``library``)."""
        with tempfile.TemporaryDirectory() as folder:
            self.cupboard(folder)                                    # the cupboard sits in qrun/
            script_run = Path(folder) / "srun"
            script_run.mkdir()
            (script_run / "questions.json").write_text(json.dumps({"chapter_title": "Monsoon", "questions": [QUESTION]}),
                                                       encoding="utf-8")
            made = film()
            made["shots"][0]["visual"].update(type="cutaway", library="ghat-wall", image_prompt="Mountain wall in monsoon rain, clouds climbing the western slope, wet green forest, painterly 3D.")
            client = FakeClient([made])
            args = SimpleNamespace(stage="films", source="", from_run=str(script_run), library=str(Path(folder) / "qrun"),
                                   videos="q01", out=str(Path(folder) / "out"), pages="", course="Class 9",
                                   language="Hinglish", model="", max_rounds=2)
            summary = vm_studio.run(args, client=client, load=None, voice_maker=lambda: (FakeVoice(), None))
            self.assertEqual((summary["status"], summary["films"][0]["kept_pictures"], client.images), ("ok", 1, 0))
            self.assertEqual([e["id"] for e in vm_studio.cupboard(args)], ["ghat-wall"])
        import codex_vm
        job = {"section": "studio", "stage": "films", "max_rounds": 5, "from_run": "https://x/s6",
               "library": "https://raw.githubusercontent.com/o/r/codex-jobs/prompts/c116-3b"}
        cmd = codex_vm.argv(job, Path("/tmp/out"), "python")
        self.assertEqual(cmd[cmd.index("--library") + 1], job["library"])

    def test_a_kept_picture_keeps_its_words(self):
        """A kept picture is already made and was chosen: its description is not sent back for its words."""
        made = film()
        made["shots"][0]["visual"].update(type="photo", library="dam", image_prompt="a photoreal hydroelectric model with "
                                          "a dense proton population and a four-item checklist")
        self.assertEqual(studio_film.crowd_problems(made) + studio_film.photo_problems(made) + studio_film.overlay_problems(made), [])
        made["shots"][0]["visual"]["library"] = ""
        self.assertEqual(len(studio_film.crowd_problems(made) + studio_film.photo_problems(made) + studio_film.overlay_problems(made)), 3)

    def test_a_moving_part_moves_enough_to_be_seen(self):
        """Navin, 24 November 2026: "photorealistic hisse abhi bhi nahi hilte": the turbine's sheen rolled but its wheel never
        turned, and a 19% wide CF1 head opened by 2.8%. A wheel facing us turns for real; a jaw moves with its size."""
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn(".part.p-wheel .pb{animation:spin", page)
        act = page[page.index("function doAct"):page.index("function addRiders")]
        self.assertIn("if(wheelLike(P))P.el.classList.add('p-wheel')", act)
        self.assertIn("const k=jawScale(P)", act)
        self.assertIn("function wheelLike(P)", page)
        self.assertIn("size/10", page[page.index("function jawScale(P)"):])

    def test_a_part_seen_from_the_side_turns_on_its_frames(self):
        """r2 of 11.6.3b (24 November 2026): the dam's turbine runner, seen from the side, did not move by a pixel. BIE
        draws its turn as frames (part_spin.py) and the player runs them while it spins, in place of the rotation."""
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn("@keyframes rollframes", page)
        self.assertIn(".part.p-roll .roll img{animation-play-state:running}", page)
        self.assertIn(".part.p-roll .pb>img,.part.p-roll .sheen{opacity:0}", page)
        maker = page[page.index("function rollEl(s)"):]
        for said in ("im.style.width=(s.n*100)+'%'", "'steps('+s.n+')'", "(+s.pitch||60)/120"):
            self.assertIn(said, maker[:600])
        act = page[page.index("function doAct"):page.index("function addRiders")]
        self.assertIn("if(P.roll)P.el.classList.add('p-roll');else if(wheelLike(P))", act)
        self.assertIn("classList.remove('p-spin','p-wheel','p-roll')", act)
        self.assertIn("roll:!!roll", page[page.index("function partEl"):page.index("function rollEl")])


class LearnedFromFilmA(unittest.TestCase):
    """Navin compared every Q14 film (21 November 2026) and chose that BIE learn from his film A: a question before every
    mechanism, everyday pictures through the film, the whole mechanism shown (a turning machine turns, a returning process
    is a wheel), molecules meeting one at a time, named as they meet and timed to the word ("achhe coordination ke saath,
    khichdi si na pake"), and one picture set per machine."""

    def shot_with(self, roman, voice, **extra):
        made = film()
        line = made["shots"][1]["sentences"][0]
        line.update(roman=roman, voice=voice, **extra)
        return made

    def test_a_turning_machine_turns(self):
        made = self.shot_with("H+ ke flow se stalk ghoomta hai aur CF1 ki shape badalti hai.", "एच प्लस के फ़्लो से स्टॉक घूमता है।")
        self.assertIn("show it turning: the turning part of the picture turns", " ".join(studio_film.mechanism_problems(made)))
        made["shots"][1]["sentences"][0]["effects"] = [{"type": "spin", "x0": 40, "x1": 60, "y0": 30, "y1": 60}]
        self.assertNotIn("show it turning", " ".join(studio_film.mechanism_problems(made)))
        # on a photo or cutaway the stalk itself turns (routeS, 23 November 2026): a turn act shows it as well
        made["shots"][1]["sentences"][0]["effects"] = []
        made["shots"][1]["sentences"][0]["acts"] = [{"part": "stalk", "do": "turn", "toward": [], "turns": -120, "rider": ""}]
        self.assertNotIn("show it turning", " ".join(studio_film.mechanism_problems(made)))

    def test_made_again_needs_a_wheel(self):
        made = self.shot_with("Akhir mein RuBP dobara banta hai.", "आख़िर में आरयूबीपी दोबारा बनता है।")
        self.assertIn("show the return as a wheel", " ".join(studio_film.mechanism_problems(made)))

    def test_molecules_meet_one_at_a_time_and_named(self):
        meeting = dict(REACT)
        made = self.shot_with("Pehle CO2 aata hai, phir kuch banta hai.", "पहले CO2 आता है।", reacts=[meeting, dict(REACT)],
                              moves=[dict(CLOUDS), dict(CLOUDS)])
        found = " ".join(studio_film.mechanism_problems(made))
        self.assertIn("2 meetings in one sentence; one meeting at a time", found)
        self.assertIn("a meeting and 2 other flows", found)
        self.assertIn("RuBP takes part in the meeting but the line does not name it", found)
        self.assertIn("a mechanism is shown here but no question is asked", found)
        good = self.shot_with("Par 3-PGA kaise banta hai? Dekhiye, CO2 RuBP se judkar 3-PGA banata hai.",
                              "पर 3-PGA कैसे बनता है? देखिए, CO2 RuBP से जुड़कर 3-PGA बनाता है।", reacts=[meeting])
        self.assertEqual([p for p in studio_film.mechanism_problems(good) if "s2" in p], [])

    def test_the_flash_comes_when_the_product_is_named(self):
        meeting = {"inputs": [{"what": "ADP", "from": [10, 40]}, {"what": "Pi", "from": [10, 60]}], "at": [50, 40],
                   "outputs": [{"what": "ATP", "to": [80, 30]}], "label": "", "ms": 4000, "loop": False}
        roman = "ATP synthase ke CF1 par ADP aur Pi aate hain, aur aakhir mein yahan ATP banta hai."
        delay = studio_film.timed([meeting], roman, 10.0)[0]["delay"]
        word = roman.lower().index("yahan atp") + len("yahan ") 
        self.assertAlmostEqual(delay + 0.45 * 4.0, word / len(roman) * 10.0, places=1)     # the flash on "ATP", not "ATP synthase"
        self.assertNotIn("delay", studio_film.timed([meeting], "Kuch hota hai.", 5.0)[0])
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn("addReact(r,now+300+(r.delay!=null?r.delay*1000:i*1400))", page)

    def test_a_question_in_half_the_shots_and_everyday_pictures(self):
        made = film()
        extra = json.loads(json.dumps(made["shots"][1]))
        for n in range(3, 6):
            made["shots"].append(dict(json.loads(json.dumps(extra)), id=f"s{n}"))
        found = " ".join(studio_film.mechanism_problems(made))
        self.assertIn("questions in 1 of 5 shots", found)
        self.assertIn("everyday picture(s) in the film", found)

    def test_glow_and_spin_are_placed_by_looking(self):
        shot = {"id": "s6", "sentences": [{"roman": "Stalk ghoomta hai.", "effects": [{"type": "spin", "x0": 70, "x1": 90, "y0": 20, "y1": 40}]}]}
        items = studio_film.place_items(shot)
        spin = [i for i in items if i["id"] == "s0.effect0"][0]
        self.assertEqual(spin["points"], [[80.0, 30.0]])
        studio_film.apply_places(items, {"items": [{"id": "s0.effect0", "visible": True, "points": [[50, 45]]}]})
        self.assertEqual(shot["sentences"][0]["effects"][0], {"type": "spin", "x0": 40, "x1": 60, "y0": 35, "y1": 55})

    def test_one_machine_keeps_one_picture_set(self):
        library = [{"id": "a-channel", "set": "A", "scale": "ATP synthase close up: channel"},
                   {"id": "b-head", "set": "B", "scale": "ATP synthase close up: head"},
                   {"id": "a-head", "set": "A", "scale": "ATP synthase close up: head"}]
        made = film()
        made["shots"][0]["visual"].update(type="cutaway", library="a-channel")
        made["shots"][1]["visual"].update(type="cutaway", library="b-head")
        self.assertIn("atp synthase close up comes from set 'B' here and from set 'A' in s1",
                      " ".join(studio_film.library_problems(made, {"library": library})))
        made["shots"][1]["visual"]["library"] = "a-head"
        self.assertEqual(studio_film.library_problems(made, {"library": library}), [])


class FirstHeadingFilms(unittest.TestCase):
    """The first two films cut from the chapter's script (11.7.2 part a, 11.6.3 part b, 23 November 2026) ended
    needs_fix after five rounds. Most rounds went to BIE's own misreadings: CO₂ and CF₀ written with subscripts were not
    found, a wheel station that became a 'dot' waited for "dot", the script's workshop analogy on two asides counted as
    0 everyday pictures, a plain "dobara" forced a wheel, a 'motor' kept picture that never existed, and the look's
    workshop clause put a motor into the chloroplast picture. The player ran an 18-carbon count off both sides and
    showed a pin and a wheel station of one name twice."""

    def wheel_shot(self, stations, *lines):
        cycle = {"x": 50, "y": 50, "rx": 20, "ry": 20, "label": "", "carriers": 1, "ms": 14000, "stations": stations}
        first = {"roman": "H⁺ CF₀ se lumen se stroma ko jaate hain.", "voice": "एच प्लस सीएफ़ ज़ीरो से जाते हैं।", "cycles": [cycle]}
        return {"shots": [{"id": "s5", "sentences": [first] + [{"roman": r, "voice": "कुछ।"} for r in lines]}]}

    def test_a_subscript_names_what_it_writes(self):
        self.assertEqual(studio_film._tokens("CO₂ aur CF₀"), studio_film._tokens("CO2 aur CF0"))
        self.assertIn("proton", studio_film._spoken_words("H⁺ jama hote hain"))
        made = LearnedFromFilmA().shot_with("Par 3-PGA kaise banta hai? Ek RuBP aur ek CO₂ milkar 3-PGA banate hain.",
                                            "पर 3-PGA कैसे बनता है? एक आरयूबीपी और एक सीओटू मिलकर 3-PGA बनाते हैं।", reacts=[dict(REACT)])
        self.assertNotIn("takes part in the meeting", " ".join(studio_film.mechanism_problems(made)))

    def test_a_wheel_station_with_a_short_name_or_a_plain_dot(self):
        stations = [{"at": 180, "label": "", "becomes": "H+", "takes": [], "gives": []},
                    {"at": 0, "label": "CF₀", "becomes": "H+", "takes": [], "gives": []}]
        made = self.wheel_shot(stations, "Return ke liye dobara proton pumping kyun nahi?", "Isliye CF₀ se return downhill hai.")
        self.assertEqual([p for p in studio_film.screen_problems(made, {}) if "station" in p], [])
        dot = [{"at": 0, "label": "RuBP", "becomes": "RuBP", "takes": [], "gives": []},
               {"at": 180, "label": "", "becomes": "dot", "takes": [], "gives": []}]
        found = " ".join(studio_film.screen_problems(self.wheel_shot(dot, "RuBP pool dobara banta hai.", "Aage badhte hain."), {}))
        self.assertNotIn("station 'dot'", found)
        self.assertIn("a station of the wheel is a plain dot with no label; label it", found)

    def test_an_aside_is_an_everyday_picture_and_a_script_film_keeps_the_scripts(self):
        made = film()
        extra = json.loads(json.dumps(made["shots"][1]))
        for n in range(3, 7):
            made["shots"].append(dict(json.loads(json.dumps(extra)), id=f"s{n}"))
        self.assertIn("0 everyday picture(s)", " ".join(studio_film.mechanism_problems(made)))
        self.assertNotIn("everyday picture(s)", " ".join(studio_film.mechanism_problems(made, {"script_lines": True})))
        made["shots"][3]["aside"] = made["shots"][4]["aside"] = True
        self.assertNotIn("everyday picture(s)", " ".join(studio_film.mechanism_problems(made)))

    def test_made_again_needs_a_making_word(self):
        shot = LearnedFromFilmA().shot_with
        for line in ("Lekin acceptor dobara kaise milta hai?", "Ab RuBP pool dobara banata hai.", "Pathway RuBP ko regenerate karta hai."):
            self.assertIn("show the return as a wheel", " ".join(studio_film.mechanism_problems(shot(line, "दोबारा।"))), line)
        self.assertNotIn("show the return as a wheel", " ".join(studio_film.mechanism_problems(
            shot("Return ke liye dobara proton pumping ki energy kyun nahi lagani?", "दोबारा प्रोटॉन पम्पिंग क्यों नहीं?"))))

    def test_the_everyday_look_stays_on_the_aside(self):
        look = ("16:9 realistic macro journey, warm soft light and matte hydrated textures; stroma cream, Rubisco teal; "
                "everyday workshop has a matte steel reusable mould and a charcoal electric motor.")
        world = "Chloroplast cutaway, cream stroma, matte biological textures, open centre for a bookkeeping wheel."
        aside = "Photorealistic everyday workshop: a steel reusable mould on a bench and an electric motor, warm light."
        self.assertNotIn("motor", studio_film.look_for(world, look))
        self.assertIn("stroma cream", studio_film.look_for(world, look))
        self.assertNotIn("motor", studio_film.look_for(world + " A workshop mould is drawn later.", look, aside=False))
        self.assertIn("reusable mould and a charcoal electric motor", studio_film.look_for(aside, look, aside=True))
        made = {"visual": {"type": "photo", "image_prompt": world + " Workshop mould shape."}, "aside": False}
        self.assertNotIn("electric motor", studio_film.image_prompt(made, look))

    def test_an_empty_cupboard_clears_a_named_picture(self):
        made = film()
        made["shots"][0]["visual"]["library"] = "motor"
        record = studio_film.write(FakeClient([made]), "m", QUESTION, max_rounds=1)
        self.assertEqual(record["film"]["shots"][0]["visual"]["library"], "")
        self.assertNotIn("no kept picture", " ".join(record["problems"]))
        kept = film()
        kept["shots"][0]["visual"]["library"] = "motor"
        self.assertIn("no kept picture 'motor'", " ".join(studio_film.library_problems(
            studio_film.without_empty_cupboard(kept, {"library": [{"id": "ghat"}]}), {"library": [{"id": "ghat"}]})))

    def test_a_wheel_moved_by_looking_stays_inside_the_picture(self):
        made = self.wheel_shot([{"at": 0, "label": "CF₀", "becomes": "H+", "takes": [], "gives": []}], "CF₀ se.")
        shot = made["shots"][0]
        items = studio_film.place_items(shot)
        wheel = [i for i in items if i["id"].endswith(".cycle0")][0]
        studio_film.apply_places(items, {"items": [{"id": wheel["id"], "visible": True, "points": [[90, 95]]}]})
        cycle = shot["sentences"][0]["cycles"][0]
        self.assertEqual((cycle["x"], cycle["y"]), (78.0, 78.0))
        self.assertNotIn("must sit inside the picture", " ".join(studio_film.motion_problems(shot["sentences"][0], set(), "s5")))

    def test_the_player_fits_a_count_and_keeps_one_label_per_name(self):
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for part in ("function fitBeads(box)", "scale(var(--fit,1))", ".beads.wrap", "!like(g,groups[i+1])",
                     "Math.hypot(l.x-x,l.y-y)<12", "l.k!==labelRound", "labelRound++", "a.dim=true", "if(ac.dim)",
                     "fxBox.querySelectorAll('.beads').forEach(o=>"):
            self.assertIn(part, page)


class SectionFilmsLook(unittest.TestCase):
    """Navin on the first heading film (23 November 2026): "starting mein chamkti arrow line agar kis cheej ki taraf flow ya
    movement ka raasta hi dikhana hai to dusra mechanism ho" (card: "Cheez khud chale"), "kheechdi si pak gayi ... wo kadi
    nhi ban paati", and "pehale wale chamakdaar tarike se hi banao video"."""

    def test_a_route_is_the_thing_itself_moving_not_a_growing_line(self):
        grow = {"points": [[20, 70], [50, 50], [80, 40]], "label": "", "ms": 3000}
        route = {"roman": "Lumen ke H⁺ ATP synthase se stroma ki taraf lautte hain.", "voice": "एच प्लस लौटते हैं।", "grows": [grow]}
        self.assertIn("show the moving thing itself travelling on the route (moves), with no line",
                      " ".join(studio_film.motion_problems(route, set(), "s2 sentence 1")))
        tube = dict(route, roman="Pollen tube style se hokar ovule ki taraf badhti hai.")
        self.assertNotIn("growing line", " ".join(studio_film.motion_problems(tube, set(), "s2 sentence 1")))
        self.assertIn('"Cheez khud chale"', studio_film.INSTRUCTIONS)
        self.assertNotIn("a root tip, a signal", studio_film.INSTRUCTIONS)
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for part in ("const TAIL=[", "tails.push(TAIL.map(", "(ac.tails[i]||[]).forEach((c,j)=>", "const hide=()=>"):
            self.assertIn(part, page)

    def test_a_glossy_picture_is_not_asked_to_be_matte(self):
        look = "16:9 macro journey, warm soft light and matte hydrated textures; stroma cream"
        shot = {"visual": {"type": "cutaway", "image_prompt": "Stroma close up, matte non-reflective proteins, cream fluid."}}
        made = studio_film.image_prompt(shot, look, "glossy")
        self.assertNotIn("matte", made.lower())
        self.assertNotIn("non-reflective", made)
        self.assertIn("warm soft light and hydrated textures", made)
        self.assertTrue(made.endswith(studio_film.CUTAWAY_SUFFIX))
        self.assertIn("matte", studio_film.image_prompt(shot, look, "mixed"))      # his 22 Nov look keeps its words
        self.assertIn("never write matte, non-reflective", studio_film.look_rule("glossy"))
        self.assertIn("{look_rule}", studio_film.INSTRUCTIONS)

    def test_a_picture_shows_what_its_lines_talk_about(self):
        made = film()
        made["shots"][0]["visual"].update(type="cutaway", image_prompt="Leaf mesophyll cutaway, cellulose walls, a large "
                                          "vacuole and chloroplasts along the wall, soft light.")
        line = made["shots"][0]["sentences"][1]
        line["roman"] = "Lumen ke H⁺ ka ATP synthase se stroma ki taraf return energy deta hai."
        self.assertIn("s1: its lines talk about ATP synthase but its picture is a whole-structure view",
                      " ".join(studio_film.picture_problems(made)))
        made["shots"][0]["visual"]["image_prompt"] = "Close molecular cutaway of the thylakoid membrane with ATP synthase right."
        self.assertEqual(studio_film.picture_problems(made), [])
        made["shots"][0]["visual"]["image_prompt"] = "Leaf mesophyll cutaway, cellulose walls, a large vacuole, soft light."
        line["part"] = "hook"                       # the opening question may ask before the journey
        self.assertEqual(studio_film.picture_problems(made), [])


class StuckCalls(unittest.TestCase):
    """The first 11.6 section job (23 November 2026) failed whole: one codex call did not finish in 30 minutes, and the
    films stage stopped with no film made."""

    def test_a_stuck_call_is_asked_once_more_and_a_later_failure_keeps_the_last_round(self):
        from bie.model_gateway.live.errors import ProviderError

        class Flaky(FakeClient):
            def __init__(self, answers, fail):
                super().__init__(answers); self.fail = list(fail); self.calls = 0
            def chat(self, *, model, messages, schema=None):
                self.calls += 1
                if self.fail and self.fail.pop(0):
                    raise ProviderError("timeout", "codex exec did not finish within 1800 s", provider="codex")
                return super().chat(model=model, messages=messages, schema=schema)

        once = Flaky([film()], [True, False])
        record = studio_film.write(once, "m", QUESTION, max_rounds=1)
        self.assertEqual(once.calls, 2)
        self.assertIsNotNone(record["film"])
        bad = film(); bad["shots"][0]["key"] = ""
        later = Flaky([bad], [False, True, True])
        record = studio_film.write(later, "m", QUESTION, max_rounds=3)
        self.assertEqual(record["film"]["shots"][0]["key"], "")
        self.assertIn("round 2: the maker's call failed", " ".join(record["problems"]))
        never = Flaky([], [True, True])
        with self.assertRaises(ProviderError):
            studio_film.write(never, "m", QUESTION, max_rounds=1)
        refused = Flaky([], [False]); refused.chat = lambda **k: (_ for _ in ()).throw(ProviderError("auth", "no", provider="codex"))
        with self.assertRaises(ProviderError):
            studio_film.write(refused, "m", QUESTION, max_rounds=1)

    def test_one_failed_film_does_not_stop_the_others(self):
        from bie.model_gateway.live.errors import ProviderError
        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "qrun"; run_dir.mkdir()
            second = dict(QUESTION, id="q02")
            (run_dir / "questions.json").write_text(json.dumps({"chapter_title": "Monsoon", "questions": [QUESTION, second]}), encoding="utf-8")
            args = SimpleNamespace(stage="films", source="", from_run=str(run_dir), videos="q01,q02", out=str(Path(folder) / "out"),
                                   pages="", course="Class 9", language="Hinglish", model="", max_rounds=1)

            class Client(FakeClient):
                def chat(self, *, model, messages, schema=None):
                    if "Ek hi hawa" in messages[1]["content"] and not hasattr(self, "q2"):
                        if not getattr(self, "n", 0) >= 2:
                            self.n = getattr(self, "n", 0) + 1
                            raise ProviderError("timeout", "codex exec did not finish within 1800 s", provider="codex")
                    return super().chat(model=model, messages=messages, schema=schema)

            summary = vm_studio.run(args, client=Client([film(), film()]), load=None, voice_maker=lambda: (FakeVoice(), None))
            rows = {r["qid"]: r for r in summary["films"]}
            self.assertTrue(rows["q01"].get("failed"))
            self.assertIn("the film was not made", rows["q01"]["problems"][0])
            self.assertFalse(rows["q02"].get("failed"))
            self.assertEqual(summary["status"], "needs_fix")
            self.assertTrue((Path(folder) / "out" / "films" / "q02.html").exists())


class PassedFilms(unittest.TestCase):
    """Seekh → BIE (CLAUDE.md): a film Navin passed must still pass every code check after any change. The first is Q14
    "A jaisi" (Navin, 21 November 2026: "isko pass maankar")."""

    def test_every_passed_film_still_passes(self):
        import gzip
        found = sorted((ROOT / "tests" / "fixtures" / "passed_outputs" / "studio").glob("*.json.gz"))
        self.assertTrue(found)
        for path in found:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                kept = json.load(f)
            self.assertIn("Navin", kept["accepted"])
            self.assertEqual(studio_film.problems(kept["film"], kept["question"]), [], path.name)


class HybridRemakeOf1163b(unittest.TestCase):
    """Navin, 24 November 2026, on r2 of 11.6.3b: the same film in his hybrid look (matte + controlled light + structure),
    the camera tied to the words, each route drawn as a structure, parts that press, pull and grip, and enough labels."""

    def test_a_job_chooses_its_look(self):
        job = codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "r3-hybrid-test", "section": "studio", "stage": "films",
                                 "from_run": "https://example.org/runs/x", "look": "mixed"})
        self.assertIn("--look", codex_vm.argv(job, Path("/tmp/out"), "python"))
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "r3-hybrid-test", "section": "studio", "stage": "films",
                               "from_run": "https://example.org/runs/x", "look": "neon"})
        hybrid = studio_film.messages({"id": "q", "question": "?", "points": []}, course="Biology", language="Hinglish",
                                      look="mixed")[0]["content"]
        self.assertIn("hybrid look (22 November 2026)", hybrid)
        self.assertNotIn("The pictures are glossy", hybrid)
        self.assertIn("hybrid look (22 November 2026)", studio_film.messages({"id": "q", "question": "?", "points": []},
                                                                           course="Biology", language="Hinglish")[0]["content"])
        self.assertIn("The pictures are glossy", studio_film.messages({"id": "q", "question": "?", "points": []},
                                                                      course="Biology", language="Hinglish",
                                                                      look="glossy")[0]["content"])
        machine = {"visual": {"type": "cutaway", "image_prompt": "ATP synthase in the thylakoid membrane, glossy"}, "sentences": []}
        whole = {"visual": {"type": "cutaway", "image_prompt": "a whole chloroplast, no individual proteins"}, "sentences": []}
        close, wide = studio_film.image_prompt(machine, "", "mixed"), studio_film.image_prompt(whole, "", "mixed")
        self.assertIn("real lipid bilayer with visible thickness", close)
        self.assertIn("controlled satin sheen", close)
        self.assertNotIn("membrane, glossy", close)                               # the maker's own "glossy" is taken out
        self.assertIn("every membrane with its real thickness", wide)

    def test_each_route_is_drawn_as_a_structure(self):
        shot = {"visual": {"type": "cutaway", "image_prompt": "ATP synthase in the membrane", "parts": []},
                "sentences": [{"pins": [{"label": "CF₀", "x": 48, "y": 58}],
                               "moves": [{"what": "H+", "label": "H⁺", "points": [[20, 85], [48, 55], [60, 20]]}]},
                              {"pins": [], "moves": [{"what": "H+", "label": "H⁺", "points": [[22, 84], [60, 22]]}]}]}
        clause = studio_film.route_clause(shot)
        self.assertIn("a real open channel in that structure", clause)
        self.assertIn("the channel through the CF₀ that H⁺ pass through, from the lower left to the upper centre", clause)
        self.assertEqual(clause.count("the channel through"), 1)                 # the same route once
        self.assertIn("draw no tube, pipe or ribbon", clause)
        self.assertIn(clause, studio_film.image_prompt(shot, "", "mixed"))
        photo = dict(shot, visual={"type": "photo", "image_prompt": "a dam"})
        self.assertEqual(studio_film.route_clause(photo), "")                    # a photo shows the real thing as it is
        self.assertEqual(studio_film.route_clause({"visual": {"type": "cutaway"}, "sentences": [{"moves": []}]}), "")

    def test_no_tube_for_things_in_open_fluid(self):
        """r3 of 11.6.3b (24 November 2026): routes of ATP, NADPH and sugar through the open stroma were drawn as invented
        tubes between the proteins. Only a route that passes a carrier gets a passage."""
        shot = {"visual": {"type": "cutaway", "image_prompt": "stroma with Rubisco", "parts": []},
                "sentences": [{"pins": [{"label": "stroma", "x": 50, "y": 40}, {"label": "biosynthetic reactions", "x": 60, "y": 50}],
                               "moves": [{"what": "ATP", "label": "ATP", "points": [[80, 30], [60, 45], [40, 50]]},
                                         {"what": "NADPH", "label": "NADPH", "points": [[10, 60], [50, 50]]}]}]}
        self.assertEqual(studio_film.route_clause(shot), "")
        shot["sentences"][0]["pins"].append({"label": "proton pump", "x": 30, "y": 55})
        shot["sentences"][0]["moves"].append({"what": "H+", "label": "H⁺", "points": [[30, 80], [30, 55], [30, 30]]})
        clause = studio_film.route_clause(shot)
        self.assertIn("the channel through the proton pump that H⁺ pass through", clause)
        self.assertNotIn("ATP pass", clause)

    def test_a_big_part_is_not_pushed_into_and_a_light_picture_dims_gently(self):
        big = [{"id": "lobe", "box": [20, 0, 78, 58]}]
        line = {"dur": 6.0, "acts": [{"part": "lobe", "do": "squeeze", "at": 1.0}], "moves": [], "reacts": []}
        self.assertEqual(studio_film.camera_track(line, big), [])                # already fills the frame
        import base64, io
        from PIL import Image
        def uri(colour):
            out = io.BytesIO()
            Image.new("RGB", (32, 18), colour).save(out, "PNG")
            return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode()
        self.assertGreater(studio_film.lightness(uri((240, 232, 215))), 0.85)   # r3's cream
        self.assertLess(studio_film.lightness(uri((10, 40, 50))), 0.2)          # the glossy films' dark teal
        self.assertIsNone(studio_film.lightness(""))
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn("dark=sh.light!=null&&sh.light>.55?.24:.62", page)

    def test_the_camera_goes_where_the_voice_is(self):
        layers = [{"id": "head", "box": [50, 20, 70, 50]}]
        line = {"dur": 6.0, "acts": [{"part": "head", "do": "squeeze", "at": 2.0}],
                "moves": [{"what": "H+", "points": [[20, 80], [40, 50], [60, 30]], "at": 3.5, "ms": 2500}], "reacts": []}
        track = studio_film.camera_track(line, layers)
        self.assertEqual((track[0]["at"], track[0]["x"], track[0]["y"]), (1.7, 60.0, 35.0))    # the head, as it is named
        self.assertTrue(studio_film.TRACK_MIN <= track[0]["scale"] <= studio_film.TRACK_MAX)
        moving = studio_film.camera_track({"dur": 6.0, "acts": [], "reacts": [],
                                           "moves": [{"what": "H+", "points": [[20, 80], [60, 30]], "at": 1.0, "ms": 2500}]}, [])
        self.assertEqual([(c["x"], c["y"]) for c in moving], [(20, 80), (60, 30)])              # followed to where it goes
        self.assertEqual(studio_film.camera_track(dict(line), layers, question=True), [])        # a question holds still
        end = studio_film.camera_track({"dur": 6.0, "acts": [], "moves": [], "reacts": []}, [], last=True)
        self.assertEqual((end[-1]["x"], end[-1]["y"], end[-1]["scale"]), (50.0, 50.0, 1.0))   # the shot ends on the whole
        self.assertLessEqual(len(studio_film.camera_track(line, layers, last=True)), 3)
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        sentence = page[page.index("function sentence(k)"):page.index("function speak(")]
        self.assertIn("tr.forEach(c=>setTimeout(()=>{if(my===token&&ki===k)camTo(c.x,c.y,", sentence)

    def test_parts_press_pull_and_grip(self):
        import sys as _sys
        _sys.path.insert(0, str(ROOT / "tests"))
        from test_film_parts import acts_film
        made = acts_film()
        lines = made["shots"][0]["sentences"]
        lines[1]["acts"][1].update(do="grab", rider="ADP")
        lines[2]["acts"].append({"part": "beta_top", "do": "suck", "toward": [60, 40], "turns": 0, "rider": ""})
        said = " ".join(studio_film.parts_problems(made))
        self.assertIn("suck on 'beta_top' needs rider: the molecule it pulls in", said)
        self.assertNotIn("grab on 'beta_top' needs rider", said)
        for act in ("squeeze", "suck", "grab"):
            self.assertIn(act, studio_film.DOES)
            self.assertIn(act, studio_film.ACT_WORDS)
        self.assertIn("squeeze (the part is pressed and gives", studio_film.INSTRUCTIONS)
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        act = page[page.index("function doAct"):page.index("function addRiders")]
        self.assertIn("if(a.do==='squeeze'){if(!instant){squash(P,now,T,.8,1500)", act)
        self.assertIn("if(a.do==='suck'&&T){if(!instant)suction(P,T,a.rider,now);return;}", act)
        self.assertIn("holdAt(T,a.rider,now,instant,P)", act)
        self.assertIn("squash(P,now+1350,T,.88,700)", act)                       # a part that sticks gives on contact
        self.assertIn("addLabel(P.name,P.c[0]", act)                              # named as it acts
        self.assertIn("scale(${(n.s*chew*px).toFixed(4)},${(n.s*chew*py).toFixed(4)})", page)

    def test_part_names_reach_the_player(self):
        film = {"shots": [{"id": "s1", "visual": {"type": "cutaway", "parts": [{"id": "head", "name": "CF₁ head"}]},
                           "sentences": [{"roman": "CF₁ head dabta hai.", "acts": [{"part": "head", "do": "squeeze"}]}]}]}
        data = studio_film.player_data(film, images={}, audio={}, chapter="", question={"id": "q"},
                                       parts={"s1": [{"id": "head", "img": "data:x", "box": [40, 20, 60, 50]}]})
        shot = data["shots"][0]
        self.assertEqual(shot["parts"][0]["name"], "CF₁ head")
        self.assertEqual(shot["sentences"][0]["acts"][0]["do"], "squeeze")
        self.assertTrue(shot["sentences"][0]["track"])                          # the camera goes to the head, then the whole


def _membrane_film():
    """A small cutaway film under the 24 November 2026 rules (its shots name their place)."""
    pins = [{"label": "Proton pump", "x": 22, "y": 55}, {"label": "CF₀", "x": 70, "y": 58}]
    return {"title": "Pump aur synthase", "look": "hybrid", "shots": [
        {"id": "s1", "title": "Membrane", "key": "Pump H⁺ andar bhejta hai", "covers": [0], "place": "Thylakoid membrane",
         "visual": {"type": "cutaway", "image_prompt": "Thylakoid membrane with a proton pump at left and ATP synthase with "
                    "its CF0 channel at right", "svg": "", "library": "",
                    "parts": [{"id": "pump", "name": "Proton pump", "looks": "teal complex in the membrane at left"}]},
         "dive": {"x": -1, "y": -1}, "aside": False,
         "sentences": [{"roman": "Thylakoid ke andar H⁺ kaise jama hote hain?", "pins": [], "moves": [], "acts": []},
                       {"roman": "Proton pump H⁺ ko stroma se pakadkar lumen mein chhodta hai.", "pins": pins[:1],
                        "moves": [], "acts": [{"part": "pump", "do": "carry", "toward": [22, 80], "turns": 0, "rider": "H+"}]},
                       {"roman": "Ab aap poochhenge ki CF₀ se H⁺ kaise lautte hain?", "pins": pins[1:], "moves": [],
                        "acts": []}]},
        {"id": "s2", "title": "Channel", "key": "CF₀ ka raasta", "covers": [0], "place": "CF₀",
         "visual": {"type": "cutaway", "image_prompt": "Close-up of the CF0 ring of ATP synthase in the membrane", "svg": "",
                    "library": "", "parts": []},
         "dive": {"x": 70, "y": 58}, "aside": False,
         "sentences": [{"roman": "Dekhiye, H⁺ CF₀ ke raaste se stroma mein lautte hain.", "pins": [],
                        "moves": [{"what": "H+", "label": "H⁺", "points": [[70, 85], [70, 40]], "count": 3, "ms": 2000,
                                   "loop": False}], "acts": []}]}]}


class LivingWorldAndQuestions(unittest.TestCase):
    """Navin, 24 November 2026, after r3 of 11.6.3b passed its hybrid look: a living membrane, a proton pump that grips H⁺
    and lets it go in the lumen, questions said as questions and shown on the screen with the camera on what they ask
    about, and a clear zoom when the film goes inside a part."""

    def test_a_question_says_that_a_question_comes(self):
        made = _membrane_film()
        self.assertEqual(studio_film.question_problems(made), [])
        made["shots"][0]["sentences"][2]["roman"] = "CF₀ se H⁺ kaise lautte hain?"
        found = studio_film.question_problems(made)
        self.assertEqual(len(found), 1)
        self.assertIn("Ab aapke man mein sawaal utha hoga", found[0])
        self.assertIn("s1 sentence 3", found[0])
        made["shots"][0]["sentences"][2]["roman"] = "Ab aapke man mein sawaal utha hoga ki CF₀ se H⁺ kaise lautte hain?"
        self.assertEqual(studio_film.question_problems(made), [])
        for shot in made["shots"]:          # a film made before these rules (no place) keeps the rules it was passed under
            shot.pop("place")
        made["shots"][0]["sentences"][2]["roman"] = "CF₀ se H⁺ kaise lautte hain?"
        self.assertEqual(studio_film.question_problems(made), [])
        self.assertIn("Ab aap poochhenge", studio_film.INSTRUCTIONS)

    def test_the_question_is_on_the_screen_and_the_camera_goes_to_what_it_asks_about(self):
        data = studio_film.player_data(_membrane_film(), images={}, audio={}, chapter="Photosynthesis", question=QUESTION)
        asked = data["shots"][0]["sentences"][2]
        self.assertEqual(asked["ask"]["q"], "CF₀ se H⁺ kaise lautte hain?")       # the opener stays in the voice only
        self.assertEqual((asked["ask"]["x"], asked["ask"]["y"]), (70.0, 58.0))      # CF₀, pinned in this shot
        self.assertEqual(asked["track"], [{"at": 0.15, "x": 70.0, "y": 58.0, "scale": 1.5, "ms": 1300}])
        opening = data["shots"][0]["sentences"][0]
        self.assertEqual(opening["ask"]["q"], "Thylakoid ke andar H⁺ kaise jama hote hain?")
        self.assertNotIn("ask", data["shots"][0]["sentences"][1])
        self.assertEqual(studio_film.question_subject("Ab sawaal uthta hai ki yeh kyun hota hai?", {}, []), None)
        self.assertEqual(studio_film.camera_track({"ask": {"q": "?"}}, [], question=True), [])

    def test_a_pump_grips_what_it_moves_and_lets_it_go(self):
        made = _membrane_film()
        self.assertEqual(studio_film.carry_problems(made), [])
        self.assertEqual(studio_film.parts_problems(made), [])
        line = made["shots"][0]["sentences"][1]
        line["acts"] = []
        line["moves"] = [{"what": "H+", "label": "H⁺", "points": [[22, 30], [22, 55], [22, 80]], "count": 2, "ms": 2000,
                          "loop": False}]
        found = studio_film.carry_problems(made)
        self.assertEqual(len(found), 1)
        self.assertIn("carry", found[0])
        line["roman"] = "H⁺ yahan pump ke bina CF₀ se lautte hain."            # a line about not pumping is left alone
        line["pins"] = []
        self.assertEqual(studio_film.carry_problems(made), [])
        bad = _membrane_film()
        bad["shots"][0]["sentences"][1]["acts"][0].update(rider="", toward=[])
        said = " ".join(studio_film.parts_problems(bad))
        self.assertIn("carry on 'pump' needs toward", said)
        self.assertIn("needs rider", said)
        self.assertIn("carry (the part grips the rider on its near side", studio_film.INSTRUCTIONS)
        fresh = _membrane_film()
        items = studio_film.place_items(fresh["shots"][0], fresh["shots"][1])      # BIE places the let-go point too
        self.assertTrue(any("lets the molecule go" in it["what"] for it in items))
        self.assertTrue(any(it["what"].startswith("the point the next shot dives into: CF₀") for it in items))
        self.assertIn("pakadkar us paar chhodta hai", studio_film.ACT_WORDS["carry"])

    def test_a_dive_goes_inside_a_new_place_that_the_picture_before_shows(self):
        made = _membrane_film()
        self.assertEqual(studio_film.place_problems(made), [])
        made["shots"][1]["place"] = "Thylakoid membrane"
        self.assertIn("same place", studio_film.place_problems(made)[0])
        made["shots"][1]["place"] = "Mitochondria"
        self.assertIn("does not show", studio_film.place_problems(made)[0])
        made["shots"][1]["place"] = ""
        self.assertIn("1 to 4 words", studio_film.place_problems(made)[0])
        self.assertIn("GOING INSIDE", studio_film.INSTRUCTIONS)

    def test_the_player_gets_the_path_of_places_and_the_living_world(self):
        made = _membrane_film()
        made["shots"].append({"id": "s3", "title": "Baandh", "key": "Baandh jaisa", "covers": [0], "place": "Baandh",
                              "visual": {"type": "photo", "image_prompt": "A real dam", "svg": "", "library": "", "parts": []},
                              "dive": {"x": -1, "y": -1}, "aside": True, "sentences": made["shots"][1]["sentences"]})
        data = studio_film.player_data(made, images={}, audio={}, chapter="Photosynthesis", question=QUESTION)
        self.assertEqual([s["path"] for s in data["shots"]], [["Thylakoid membrane"], ["Thylakoid membrane", "CF₀"], None])
        self.assertEqual([s["alive"] for s in data["shots"]], [True, True, False])
        page = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for needed in ("function aliveStep(", "function carry(", "function askStep(", "function setPath(",
                       "camTo(s.dive.x,s.dive.y,2,750)", "canvas.alive"):
            self.assertIn(needed, page)
        self.assertIn("living, flexible sheet", studio_film.CUTAWAY_STYLES["close_up"])
