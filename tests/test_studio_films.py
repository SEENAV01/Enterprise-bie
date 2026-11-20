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
from bie.brain import studio, studio_film  # noqa: E402
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
         "sentences": [sentence("Yeh Ghat ki deewar baarish kyun rokti hai?", "यह घाट की दीवार बारिश क्यों रोकती है?", ["Ghat"]),
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
        self.assertIn("transparent cross-section", studio_film.image_prompt(shot))
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
        sentence("Stroma mein CO2 aata hai aur RuBP se judkar 3-PGA banta hai.", "स्ट्रोमा में CO2 आता है और RuBP से जुड़कर 3-PGA बनता है।"),
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
        shot = {"visual": {"type": "cutaway", "image_prompt": "The inside of a chloroplast", "svg": ""}}
        prompt = studio_film.image_prompt(shot, "emerald thylakoids, amber stroma glow")
        self.assertIn("Same look as the other pictures of this film: emerald thylakoids", prompt)
        self.assertIn("No text", prompt)

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
                    seen["user"] = messages[1]["content"]
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
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({"job": "bie.vm-job/1", "id": "studio-films-x", "section": "studio", "stage": "films"})


if __name__ == "__main__":
    unittest.main()
