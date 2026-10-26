"""The shot-list director (Task 046, Part A): one spoken sentence → one shot, decided by code.

Input: a passed script (a ``lesson_plan.json`` video: beats with ``say``, ``on_screen``, ``covers_item_ids``, ``purpose``,
``part_id``), the chapter map (items with ``content_type``, ``kind`` and the Task 045d unpack's ``visual_verb``), the
course's level profile and the capability vocabulary (``bie/toolbox/capabilities.json``). Output: ``shots/<video>.json``
and ``SHOTS.md``: one shot per spoken sentence (benchmark rule B-01) with its duration from ``video/timing.py``, its
block, capability and visual level (``rulebook/visual_levels.json``), the assets it wants, the camera move, the labels
and the caption; the per-level split; the checks (blocking and advisory) and the 25-rule table (12 benchmark rules,
11 visual grammar rules, W-01, LOOK-01).

It extends ``bie/brain/director.py`` (the AI scene planner of Section 3) instead of replacing it: the scenes are one per
script part (VG-01, one world, the camera moves to the next part), the beat timeline is the same ``timing.build`` the
visual section uses, and ``to_director_video`` gives the AI director's scene shape, so ``visual.run_visual`` and
``to_scene_spec`` consume a code shot list unchanged. The licence gate stays where it is: this module only names the
asset sources a lesson may use (the resolver lists them through ``licence_policy``); ``AssetLibrary.require_lesson``
runs when the files are fetched in the visual section.

Navin, 26 October 2026: content decides the scene plan; the scene plan decides the visual level the video code is made
at. The level rule has two stars (``visual_levels.json``, ``targets``): A, the chapter or book target, "90 se 99 percent
videos L3 ya isse upar" counted by each video's main level (the level with most shot-seconds), a target to work towards and
never a blocker; B, the shot level, "poori video ek level ki bane, ye zaroori nahi": every shot carries its own level from
the content, L3 or above where the content allows, L2 only where a flat drawing shows the point better with the reason on
the shot. The pace is the visual-change rate (a block or camera change, or the lit structure moving): micro biology 3-5 s
per change, engineering and physics 10-20 s; where the picture would hold longer, the director adds a camera move.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from . import hinglish, soul
from .video import timing

SCHEMA = "bie.brain.shots/1"
VERSION = "shots/1"
RULEBOOK_DIR = Path(__file__).resolve().parent / "rulebook"
LEVELS_PATH = RULEBOOK_DIR / "visual_levels.json"
GRAMMAR_PATH = RULEBOOK_DIR / "visual_grammar.json"
BENCHMARK_PATH = RULEBOOK_DIR / "benchmarks" / "epithelium_animation.json"

# Benchmark blocks (built in Task 046) and the grammar blocks every shot may add; the toolbox blocks come from capabilities.json.
WORLD_BLOCKS = {"cell_sheet", "model_3d", "cell_sheet_3d", "molecule_3d", "protein_3d", "earth_section", "orbits", "sky_dome",
                "plate_frames", "collision_3d"}
OVERLAY_LEVEL = "L3"              # a caption, a label, an arrow, a board: L3 work on top of the world
SHORT_SENTENCE_WORDS = 2          # "Kaisi?" joins the sentence that answers it (one thought, one shot)
MICRO_PACE_SECONDS = 6.0          # B-01: a shot is 3-5 s; a clause longer than this is reported (the pace itself is VG-01's change rate)
CLAUSE_SPLIT = re.compile(r"(?<=[।?!.;])\s+")     # a semicolon clause is spoken as its own thought: its own shot
MEMBER_SECONDS = (30.0, 60.0)     # B-02 "about 40-50 s per family member", with room for a book that says more or less

DEVANAGARI = soul.DEVANAGARI
WORD = re.compile(r"[A-Za-z][A-Za-z’'\-]*|[ऀ-ॿ]+")

# Words that point to a shot kind (English, Hinglish in Roman and Devanagari forms). All lower case; matched as words.
ORGAN_WORDS = ("skin", "lung", "lungs", "alveolus", "alveoli", "air sac", "air sacs", "sac", "sacs", "kidney", "tubule", "tubules",
               "bowman", "intestine", "intestines", "gut", "mouth", "bladder", "ureter", "urethra", "vessel", "vessels", "capillary",
               "capillaries", "trachea", "airway", "airways", "respiratory", "digestive", "vagina", "epidermis", "throat", "mammary",
               "salivary", "stomach", "oesophagus", "esophagus", "heart", "आँत", "मुँह", "त्वचा", "फेफड़", "गुर्द", "नली", "नलियाँ", "नलियों")
WHERE_WORDS = ("में मिलता", "में मिलती", "में मिलते", "में होता", "में होती", "में होते", "में भी", "में देखो", "में इन्हें", "में इसके",
               "के स्थान", "स्थान हैं", "इसके स्थान", "found in", "lines the", "line the", "where found", "मिलता है", "मिलती है")
MOTION_WORDS = ("absorb", "absorbs", "absorption", "secrete", "secretes", "secretion", "diffuse", "diffusion", "exchange", "cross",
                "crosses", "pass", "passes", "filter", "filters", "move", "moves", "movement", "sweep", "sweeps", "beat", "mucus",
                "flow", "stretch", "stretches", "shed", "shedding", "renew", "renewal", "transport", "trap", "traps", "push", "fold",
                "folds", "release", "carry", "carries", "wave", "flexible", "contract", "pump",
                "पार", "सोख", "बहा", "हिल", "हिलकर", "हिलने", "फैल", "फैलती", "फैलने", "झड़", "झड़ती", "मुड़", "मुड़कर", "छोड़", "छोड़ती",
                "ले जा", "ले जाती", "आगे", "अंदर आती", "वापस", "पकड़ता", "रगड़", "घिस", "दबता", "बनाकर", "निकल")
INSIDE_WORDS = ("के नीचे", "नीचे क्या", "sheet के नीचे", "अंदर की", "भीतर", "cross-section", "cross section", "cut open", "अंदर क्या",
                "के बीच", "between the cells", "underneath", "beneath", "आधार", "base")
COMPARE_WORDS = ("फर्क", "फ़र्क", "versus", " vs ", "तुलना", "जबकि", "से अलग", "compare", "comparison", "unlike", "whereas",
                 "true stratified", "simple से", "के उलट")
PANEL_CAPABILITIES = {"tree_hierarchy": ("classification",), "timeline": ("timeline",), "flowchart": ("process",),
                      "process_cycle": ("process",), "chart_bar_line_pie": ("facts_numbers",), "table_build": ("comparison", "facts_numbers"),
                      "function_graph": ("facts_numbers", "process"), "equation_transform": ("process", "facts_numbers"),
                      "reaction_steps": ("process",), "case_card": ("facts_numbers", "definition"), "network_graph": ("structure", "process"),
                      "circuit_diagram": ("structure", "process"), "board_build": (), "mnemonic_card": (), "split_compare": ()}
SIZE = re.compile(r"\d[\d.,]*\s*(?:µm|um|nm|mm|cm|km|m|kg|g|mg|ml|l|%|x|MB|GB|KB|गुना|times|fold|percent|सेकंड|seconds?|minutes?|मिनट|घंटे)(?![a-z])",
                  re.IGNORECASE)
NAME_WORDS = ("यानी", "नाम", "कहते", "कहलाता", "कहलाती", "कहलाते", "called", "named", "naam", "kehte", "kahte", "means")
STRUCTURE_WORDS = ("cell", "cells", "sheet", "sheets", "layer", "layers", "membrane", "nucleus", "nuclei", "cilia", "microvilli",
                   "keratin", "tile", "tiles", "cube", "cubes", "pillar", "pillars", "duct", "gland", "junction", "junctions",
                   "cytoplasm", "fibre", "fibres", "fiber", "base", "boundary", "barrier", "covering", "lining", "surface",
                   "projection", "projections", "row", "stack", "tissue", "organ", "organs", "cavity", "cavities", "epithelium",
                   "epithelial", "squamous", "cuboidal", "columnar", "stratified", "pseudostratified", "transitional", "keratinised",
                   "ciliated", "glandular", "urothelium", "capsule", "tubule", "tubules", "vessel", "vessels", "alveolus", "droplet",
                   "droplets", "particles", "substance", "substances", "mucus", "material", "space", "spaces", "gap", "gaps",
                   "चादर", "परत", "तह", "तहें", "तहों", "पासे", "पासा", "रेशों", "दीवार", "जोड़", "आधार", "गद्दी")
GENERIC_THINGS = frozenset(("cell", "cells", "tissue", "organ", "organs", "layer", "layers", "surface", "base", "row", "stack", "space",
                            "spaces", "gap", "gaps", "material", "substance", "substances", "boundary", "covering", "lining", "sheet",
                            "sheets", "particles", "droplet", "droplets", "tile", "tiles", "cube", "cubes", "pillar", "pillars"))
MEMBERS = (("simple squamous", ("simple squamous", "squamous की पतली", "flat cells", "thin squamous")),
           ("stratified squamous", ("stratified squamous", "layered squamous")),
           ("simple cuboidal", ("simple cuboidal", "cuboidal epithelium", "cuboidal absorption")),
           ("stratified cuboidal", ("stratified cuboidal",)),
           ("simple columnar", ("simple columnar", "columnar protection")),
           ("stratified columnar", ("stratified columnar",)),
           ("pseudostratified", ("pseudo-stratified", "pseudostratified", "pseudo और true", "pseudo में")),
           ("transitional", ("transitional", "urothelium")),
           ("keratinised", ("keratinised", "keratinized", "keratin")),
           ("ciliated", ("ciliated", "cilia")),
           ("glandular", ("gland cells", "multicellular gland", "glandular", "secretion के लिए")))
FAMILY_WORDS = (("biology_medical", ("biolog", "zoolog", "botan", "anatomy", "physiolog", "medic", "tissue", "cell", "life science",
                                     "science and technology", "general science", "environment", "ecolog", "nursing", "health")),
                ("chemistry", ("chemist", "organic", "inorganic")),
                ("physics", ("physic", "mechanic", "optic", "electricity", "magnet")),
                ("maths_statistics", ("math", "statistic", "algebra", "calculus", "geometry", "quantitative")),
                ("computer_science", ("computer", "programming", "software", "informat")),
                ("electrical_electronics", ("electrical", "electronic")),
                ("mechanical_civil", ("mechanical engineering", "civil", "structural", "thermodynam")),
                ("earth_science", ("geolog", "earth science", "seismo", "meteorolog")),
                ("astronomy_space", ("astronom", "space science", "cosmolog")),
                ("aerospace", ("aero", "aircraft", "flight")),
                ("geography_history_polity", ("geograph", "histor", "polity", "political", "civics", "constitution")),
                ("economics_commerce_management", ("econom", "commerce", "account", "management", "business", "finance")),
                ("law", ("law", "legal", "jurisprud")),
                ("psychology_education_sociology", ("psycholog", "education", "sociolog", "pedagog")),
                ("languages_literature", ("literature", "language", "hindi", "english", "sanskrit", "grammar")))


class ShotsError(ValueError):
    pass


# ---------------------------------------------------------------- data files

@lru_cache(maxsize=2)
def load_levels(path: str = str(LEVELS_PATH)) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "bie.brain.visual-levels/1":
        raise ShotsError(f"{Path(path).name}: schema must be bie.brain.visual-levels/1")
    data["_rank"] = {lvl["id"]: lvl["rank"] for lvl in data["levels"]}
    return data


@lru_cache(maxsize=2)
def load_grammar(path: str = str(GRAMMAR_PATH)) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


@lru_cache(maxsize=2)
def load_benchmark(path: str = str(BENCHMARK_PATH)) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def level_rank(level: str, levels: dict | None = None) -> int:
    return (levels or load_levels())["_rank"].get(level, 0)


def higher(a: str, b: str, levels: dict | None = None) -> str:
    return a if level_rank(a, levels) >= level_rank(b, levels) else b


def pace_band(family: str, levels: dict | None = None) -> tuple:
    """(band name, (low, high) seconds per visual change) for a subject family, or ("", None) when Navin set no target yet."""
    levels = levels or load_levels()
    for name, band in (levels.get("pace") or {}).get("bands", {}).items():
        if family in band.get("families", []):
            return name, (float(band["seconds"][0]), float(band["seconds"][1]))
    return "", None


def is_visual_change(shot: dict, previous: dict | None) -> bool:
    """Navin's measure (26 October 2026): a shot changes the picture when its block differs from the shot before or its camera
    moves. A label or a glow moving to another structure is not counted: it is too small a change to carry the pace."""
    return previous is None or shot["block"] != previous["block"] or shot["camera"] != "hold"


def visual_changes(shots: list) -> list:
    """The shot ids where the picture changes (VG-01's measure: a block or camera change)."""
    out, previous = [], None
    for shot in shots:
        if is_visual_change(shot, previous):
            out.append(shot["shot_id"])
        previous = shot
    return out


PACE_MOVES = ("zoom_in", "orbit", "zoom_out")


def pace_pass(shots: list, band: tuple | None) -> int:
    """Navin, 26 October 2026: where consecutive clauses would hold the same picture past the band's upper bound, the camera
    moves on that clause (a zoom on the lit structure, an orbit, a zoom out) so the picture changes within it. Returns how
    many camera moves were added; the shots are changed in place."""
    if not band:
        return 0
    high = band[1]
    added, since, previous = 0, 0.0, None
    for shot in shots:
        change = is_visual_change(shot, previous)
        if not change and since + shot["seconds"] > high:
            shot["camera"] = "zoom_in" if shot.get("focus") and previous.get("camera") != "zoom_in" else PACE_MOVES[added % len(PACE_MOVES)]
            shot["why"].append(f"pace: the camera moves so the picture changes within {high:g} s (VG-01)")
            added += 1
            change = True
        since = shot["seconds"] if change else since + shot["seconds"]
        previous = shot
    return added


def pace_report(shots: list, band_name: str, band: tuple | None, *, before: int, added: int) -> dict:
    total = sum(s["seconds"] for s in shots)
    changes = visual_changes(shots)
    spc = round(total / len(changes), 2) if changes else 0.0
    return {"band": band_name or "none", "target_seconds": list(band) if band else None, "changes": len(changes),
            "seconds_per_change": spc, "per_minute": round(len(changes) / total * 60, 1) if total else 0.0,
            "camera_moves_added": added, "seconds_per_change_before": round(total / before, 2) if before else 0.0,
            "within_target": bool(band and band[0] <= spc <= band[1]) if band else None}


def subject_family(subject: str) -> str:
    text = (subject or "").lower()
    for family, words in FAMILY_WORDS:
        if any(w in text for w in words):
            return family
    return "all_subjects"


# ---------------------------------------------------------------- sentences and words

def split_sentences(say: str) -> list:
    """The spoken sentences of a beat (B-01: one sentence, one shot); a sentence of one or two words joins the next one
    ("Kaisi? Irregular." is one thought), the last short one joins the one before it."""
    parts = [s.strip() for s in CLAUSE_SPLIT.split((say or "").strip()) if s.strip()]
    out = []
    carry = ""
    for sentence in parts:
        if carry:
            sentence = carry + " " + sentence
            carry = ""
        if len(sentence.split()) <= SHORT_SENTENCE_WORDS:
            carry = sentence
            continue
        out.append(sentence)
    if carry:
        if out:
            out[-1] = out[-1] + " " + carry
        else:
            out.append(carry)
    return out


def _lower(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def _has(text: str, words) -> list:
    low = _lower(text)
    found = []
    for w in words:
        w = w.lower()
        if DEVANAGARI.search(w) or " " in w or not w.isalpha():
            if w in low:
                found.append(w.strip())
        elif re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
            found.append(w)
    return found


def english_terms(sentence: str) -> list:
    """The English words of a sentence that name things (content words; the Hindi grammar words of the STOP list left out)."""
    seen, out = set(), []
    for word in re.findall(r"[A-Za-z][A-Za-z’'\-]{2,}", sentence or ""):
        low = word.lower().strip("’'-")
        if low in soul.STOP or len(low) < 3 or low in seen:
            continue
        seen.add(low)
        out.append(low)
    return out


def book_vocabulary(items_by_id: dict, item_ids) -> set:
    """Content words of the book lines of a video (its items, their parents and their unpack terms): what may be labelled."""
    words = soul.book_words(items_by_id, item_ids)
    for iid in item_ids or []:
        item = items_by_id.get(iid) or {}
        for term in (item.get("unpack") or {}).get("terms") or []:
            words |= soul.content_words(term.get("term", ""))
    return words


def member_of(sentence: str) -> str:
    low = _lower(sentence)
    for member, words in MEMBERS:
        if any(w in low for w in words):
            return member
    return ""


# ---------------------------------------------------------------- choosing the shot

def _item_context(items_by_id: dict, item_ids) -> dict:
    verbs, types, kinds = [], [], []
    for iid in item_ids or []:
        item = items_by_id.get(iid) or {}
        verb = ((item.get("unpack") or {}).get("visual_verb") or "").strip()
        if verb:
            verbs.append(verb)
        types.append(item.get("content_type", ""))
        kinds.append(item.get("kind", ""))
    return {"visual_verbs": verbs, "content_types": [t for t in types if t], "kinds": [k for k in kinds if k]}


def world_of(video: dict, items_by_id: dict, toolbox, levels: dict) -> dict:
    """The topic's one world (VG-01): the 3D capability the items' visual verbs point to most, else the top capability,
    else the kinetic caption on a dark field."""
    from ..toolbox import resolver
    counts = {}
    for beat in video.get("beats") or []:
        ctx = _item_context(items_by_id, beat.get("covers_item_ids"))
        text = " ".join(ctx["visual_verbs"] + [beat.get("on_screen", "")])
        for rank, cid in enumerate(resolver.match(text, toolbox=toolbox)):
            counts[cid] = counts.get(cid, 0) + (3 - rank)
    three_d = {cid: n for cid, n in counts.items() if level_rank(toolbox.capabilities[cid].default_level, levels) >= level_rank("L4", levels)}
    pool = three_d or counts
    if not pool:
        cap = toolbox.capabilities["kinetic_caption"]
        return {"capability": cap.id, "block": cap.blocks[0], "level": cap.default_level, "votes": 0}
    cid = max(sorted(pool), key=lambda c: pool[c])
    cap = toolbox.capabilities[cid]
    return {"capability": cid, "block": cap.blocks[0], "level": cap.default_level, "votes": pool[cid]}


def choose(sentence: str, beat: dict, ctx: dict, world: dict, toolbox, levels: dict, *, first_in_video: bool, first_in_scene: bool,
           previous: dict | None, family: str = "all_subjects") -> dict:
    """The shot's capability, blocks, level, camera and what it shows, from the sentence, the beat's purpose and the
    items' visual verbs. Order: the benchmark's named shots first (board, memory card, split, organ zoom, motion), then the
    visual verb's capability, then the world with a focus glow."""
    from ..toolbox import resolver
    low = _lower(sentence)
    purpose = beat.get("purpose", "")
    marks = soul.markers(sentence)
    question = "?" in sentence
    overlays = ["kinetic_caption"]                       # B-08: the spoken words on top of every shot
    reasons = []
    cap_id, blocks, camera = None, [], "hold"
    organ = _has(sentence, ORGAN_WORDS)
    where = _has(sentence, WHERE_WORDS)
    motion = _has(sentence, MOTION_WORDS)
    inside = _has(sentence, INSIDE_WORDS)
    compare = _has(sentence, COMPARE_WORDS)
    world_is_3d = level_rank(world["level"], levels) >= level_rank("L4", levels)

    def fitting(found):
        """Capabilities of the subject's family (or of every subject) that keep one world (VG-01): another 3D world than
        the topic's (a protein, a map, the earth's layers) is never cut to; a panel (a tree, a timeline, a chart, a board)
        may be, when the items' content type asks for it; a split screen only on a comparison."""
        out = []
        for cid in found:
            cap = toolbox.capabilities.get(cid)
            if cap is None or cid in ("kinetic_caption", "text_kinetic", "focus_glow"):
                continue
            if family not in cap.families and "all_subjects" not in cap.families:
                continue
            if level_rank(cap.default_level, levels) >= level_rank("L4", levels):
                if cid != world["capability"]:
                    continue
            elif cid in PANEL_CAPABILITIES:
                needs = PANEL_CAPABILITIES[cid]
                if needs and not set(needs) & set(ctx["content_types"]):
                    continue
                if cid == "split_compare" and not (compare or purpose == "compare"):
                    continue
            else:
                continue
            out.append(cid)
        return out
    members_named = {member for member, words in MEMBERS if any(w in low for w in words)}
    verbs_caps = fitting(resolver.match(" ".join(ctx["visual_verbs"] + [beat.get("on_screen", "")]), toolbox=toolbox))
    sentence_caps = fitting(resolver.match(sentence, toolbox=toolbox))

    if len(members_named) >= 3 and purpose in ("explain", "hook") and not compare:
        cap_id, blocks = "tree_hierarchy", ["tree_build"]
        reasons.append(f"family overview ({len(members_named)} members named) → the family tree builds")
    elif purpose == "exam_tip" or ("memory" in marks and purpose in ("recap", "exam_tip")):
        cap_id, blocks = "mnemonic_card", ["mnemonic_card"]
        reasons.append("memory beat → mnemonic card")
    elif purpose == "recap" and not question:
        cap_id, blocks = "board_build", ["board_build"]
        reasons.append("recap → the A → B board that fills (B-07)")
    elif (purpose == "compare" or compare) and not question and world_is_3d:
        cap_id, blocks = "split_compare", ["split_compare", world["block"]]
        reasons.append(f"comparison ({', '.join(compare[:2]) or 'compare beat'}) → split screen (VG-07)")
    elif organ and (where or first_in_video or purpose == "hook"):
        cap_id, blocks, camera = "organ_zoom", ["organ_zoom", world["block"]], "zoom_in"
        reasons.append(f"where found ({', '.join(organ[:3])}) → zoom from the organ to the sheet (B-09)")
    elif motion and purpose not in ("recap",) and world_is_3d:
        cap_id, blocks = "particle_flow", ["particle_flow", world["block"]]
        reasons.append(f"function or process ({', '.join(motion[:3])}) → motion over the world (B-04, VG-08)")
    elif inside and world_is_3d:
        cap_id, blocks = world["capability"], ["cutaway", world["block"]]
        reasons.append(f"the inside or the base ({inside[0]}) → cutaway of the world (VG-03)")
    elif verbs_caps:
        cap = toolbox.capabilities[verbs_caps[0]]
        cap_id = cap.id
        blocks = [cap.blocks[0]] + ([world["block"]] if world_is_3d and cap.blocks[0] not in WORLD_BLOCKS and cap.id != world["capability"] else [])
        reasons.append(f"visual verb → {cap.id}")
    elif sentence_caps:
        cap = toolbox.capabilities[sentence_caps[0]]
        cap_id, blocks = cap.id, [cap.blocks[0]] + ([world["block"]] if world_is_3d and cap.blocks[0] not in WORLD_BLOCKS else [])
        reasons.append(f"sentence words → {cap.id}")
    else:
        cap_id, blocks = world["capability"], [world["block"]]
        reasons.append("the world stays; the named structure glows (B-10)")

    structures = _has(sentence, STRUCTURE_WORDS)
    if structures and "focus_glow" not in blocks and cap_id not in ("board_build", "mnemonic_card"):
        overlays.append("focus_glow")                    # B-10: the one structure the sentence is about is lit
    if "yaani" in marks:
        reasons.append("term opened with yaani → the plain meaning on the caption at once (B-05)")
    if ("why" in marks or _has(sentence, NAME_WORDS)) and cap_id not in ("board_build", "mnemonic_card", "split_compare"):
        overlays.append("concept_arrow")                 # B-06: every name gets its reason, A → B
    if SIZE.search(sentence) and "scale_compare" not in blocks:
        overlays.append("scale_compare")                 # VG-04: a size against a known thing
    overlays.append("leader_label")                      # VG-02: labels are code text with a leader line

    # Level: the world's level while the world is on screen, else the block's default; overlays never lower it.
    main_cap = toolbox.capabilities.get(cap_id)
    level = main_cap.default_level if main_cap else OVERLAY_LEVEL
    if world["block"] in blocks:
        level = higher(level, world["level"], levels)
    level_reason = ""
    if level == "L2":                                     # Navin, 26 October 2026: L2 only where it shows the point better, with the reason
        level_reason = f"L2: a flat drawing shows this better ({main_cap.label if main_cap else cap_id})"
        reasons.append(level_reason)
    # Camera (VG-01): establish once, move to the next part, zoom from the organ, otherwise hold; no cuts.
    if first_in_video:
        camera = "establish" if camera == "hold" else camera
    elif first_in_scene and camera == "hold":
        camera = "pan"
    elif previous and previous.get("capability") == "organ_zoom" and camera == "hold":
        camera = "zoom_out" if cap_id == "organ_zoom" else "hold"
    return {"capability": cap_id, "blocks": blocks + [o for o in overlays if o not in blocks], "level": level, "camera": camera,
            "level_reason": level_reason, "reasons": reasons, "markers": marks, "question": question, "structures": structures,
            "organ": organ, "motion": motion}


THING_WORDS = frozenset(STRUCTURE_WORDS) | frozenset(ORGAN_WORDS)


def shot_labels(sentence: str, vocabulary: set, structures: list) -> list:
    """What the shot labels (B-03 said = shown): the things the sentence names, as the phrase said ("basement membrane",
    "kidney tubules", "simple squamous"): a run of the book's words that ends in a structure or organ word, at most three
    words long, in sentence order; a Hindi structure word on its own; never a word the sentence does not say."""
    labels, seen = [], set()
    text = sentence or ""
    tokens = [(m.group(0).lower().strip("’'-"), m.start(), m.end()) for m in WORD.finditer(text)]
    run, last_end = [], None
    for low, start, end in tokens + [("", len(text), len(text))]:
        known = low and not DEVANAGARI.search(low) and low not in soul.STOP and (low in vocabulary or low in THING_WORDS)
        adjacent = last_end is None or text[last_end:start].strip() == ""       # a comma or "और" between words ends the phrase
        if known and (adjacent or not run):
            run.append(low)
            last_end = end
            continue
        last_end = end if known else None
        if run:
            segment_start = 0
            for i, w in enumerate(run):                      # a phrase ends at each thing word: "packed cells", "continuous sheet"
                if w in THING_WORDS:
                    phrase = " ".join(run[max(segment_start, i - 2):i + 1])
                    if phrase not in seen:
                        seen.add(phrase)
                        labels.append(phrase)
                    segment_start = i + 1
            run = [low] if known else []
    for word in structures:
        if DEVANAGARI.search(word) and word not in seen:
            seen.add(word)
            labels.append(word)
    return labels[:6]


def caption_of(sentence: str) -> dict:
    """B-08: the spoken words on top, the English terms coloured, the Hindi in white; the yaani half marked (B-05)."""
    text = hinglish.subtitle_text(sentence)
    terms = english_terms(sentence)
    yaani = soul.YAANI.search(sentence)
    return {"text": text, "terms": terms, "yaani": sentence[yaani.end():].strip(" ,;:") if yaani else ""}


# ---------------------------------------------------------------- building the shot list

def scenes_of(beats: list) -> list:
    """One scene per script part in beat order (VG-01: one world, the camera moves to the next part); the hook before
    the first part joins it, the closing beats join the last part."""
    scenes, current = [], None
    for beat in beats:
        pid = beat.get("part_id") or ""
        if current is None:
            current = {"scene_id": "s1", "part_id": pid, "beat_ids": [beat["beat_id"]]}
            scenes.append(current)
        elif not current["part_id"] and pid:
            current["part_id"] = pid                          # the hook before the first part belongs to that part
            current["beat_ids"].append(beat["beat_id"])
        elif pid and pid != current["part_id"]:
            current = {"scene_id": f"s{len(scenes) + 1}", "part_id": pid, "beat_ids": [beat["beat_id"]]}
            scenes.append(current)
        else:
            current["beat_ids"].append(beat["beat_id"])       # a closing beat without a part stays with the last part
    return scenes


def _level_profile(course, chapter: dict) -> dict:
    from . import level as level_module
    pid = chapter.get("level") if isinstance(chapter.get("level"), str) else (chapter.get("level") or {}).get("profile_id")
    pid = pid or getattr(course, "level", "") or ""
    try:
        profiles = level_module.load()
        profile = profiles.get(pid) if pid else profiles.get(profiles.default)
        return {"id": profile.id, "name": profile.name}
    except Exception:                      # noqa: BLE001 - a missing profile never stops a shot list; it is reported
        return {"id": pid or "unknown", "name": ""}


def build_video(video: dict, chapter: dict, course, *, toolbox=None, voice: dict | None = None, levels: dict | None = None,
                grammar: dict | None = None) -> dict:
    """The shot list of one passed script."""
    from ..toolbox import registry as registry_module
    from ..toolbox import resolver
    from ..toolbox import licence as licence_policy

    toolbox = toolbox or registry_module.load()
    levels = levels or load_levels()
    grammar = grammar or load_grammar()
    items_by_id = chapter.get("items") or {}
    if isinstance(items_by_id, list):
        items_by_id = {i["item_id"]: i for i in items_by_id}
    beats = video.get("beats") or []
    if not beats:
        raise ShotsError(f"{video.get('video_id', '?')}: no beats")
    scenes = scenes_of(beats)
    timeline = timing.build(beats, scenes, voice=voice)
    family = subject_family(getattr(course, "subject", "") or (chapter.get("course") or {}).get("subject", ""))
    profile = _level_profile(course, chapter)
    world = world_of(video, items_by_id, toolbox, levels)
    all_items = sorted({iid for b in beats for iid in b.get("covers_item_ids") or []})
    vocabulary = book_vocabulary(items_by_id, all_items)
    shots, resolutions, scene_rows = [], {}, []
    first_use, seen_terms = {}, set()
    scene_start = 0.0
    previous = None
    member = ""
    for scene in scenes:
        tl = timeline[scene["scene_id"]]
        scene_shots = []
        for n, bid in enumerate(scene["beat_ids"]):
            beat = next(b for b in beats if b["beat_id"] == bid)
            ctx = _item_context(items_by_id, beat.get("covers_item_ids"))
            sentences = split_sentences(beat.get("say", ""))
            start_frame, frames = tl["beats"][bid]
            total_chars = sum(len(s) for s in sentences) or 1
            at = start_frame
            for k, sentence in enumerate(sentences):
                share = len(sentence) / total_chars
                length = round(frames * share) if k < len(sentences) - 1 else frames - (at - start_frame)
                length = max(length, 1)
                choice = choose(sentence, beat, ctx, world, toolbox, levels, first_in_video=not shots, first_in_scene=not scene_shots,
                                previous=previous, family=family)
                member = member_of(sentence) or (member if scene["part_id"] == (previous or {}).get("part_id") else "")
                labels = shot_labels(sentence, vocabulary, choice["structures"])
                terms_new = [t for t in english_terms(sentence) if t in vocabulary and t in THING_WORDS and t not in seen_terms
                             and t not in GENERIC_THINGS]
                for t in terms_new:
                    first_use[t] = f"{bid}.{k + 1}"
                seen_terms.update(t for t in english_terms(sentence))
                opened_in_beat = bool(soul.YAANI.search(beat.get("say", "")) or soul.EXAMPLE.search(beat.get("say", "")))
                if choice["capability"] not in resolutions:
                    resolutions[choice["capability"]] = resolver.resolve(choice["capability"], subject=family, level=profile["id"],
                                                                        path="web", toolbox=toolbox, log=None,
                                                                        context=f"{video.get('video_id')} {bid}")
                res = resolutions[choice["capability"]]
                procedural = choice["capability"] in ("cell_sheet_3d", "particle_flow", "organ_zoom", "focus_glow", "kinetic_caption",
                                                      "concept_arrow", "board_build", "mnemonic_card", "split_compare", "text_kinetic")
                shot = {
                    "shot_id": f"{bid}.{k + 1}", "scene_id": scene["scene_id"], "beat_id": bid, "part_id": scene["part_id"],
                    "purpose": beat.get("purpose", ""), "sentence": sentence, "member": member,
                    "start": round(scene_start + at / tl["fps"], 2), "seconds": round(length / tl["fps"], 2),
                    "frames": [int(at), int(length)], "fps": tl["fps"],
                    "capability": choice["capability"], "block": choice["blocks"][0], "blocks": choice["blocks"],
                    "level": choice["level"], "level_reason": choice["level_reason"], "camera": choice["camera"], "labels": labels,
                    "focus": next((l for l in labels if "focus_glow" in choice["blocks"]), ""), "caption": caption_of(sentence),
                    "first_use": terms_new, "opened_in_beat": opened_in_beat, "markers": choice["markers"], "question": choice["question"],
                    "items": list(beat.get("covers_item_ids") or []), "basis": beat.get("basis", ""),
                    "assets": {"procedural": procedural, "wanted": labels[:3] if not procedural else [],
                               "sources": list(res.assets), "draw": list(res.draw)[:3], "not_for_lessons": list(res.not_for_lessons),
                               "licence_gap": res.licence_gap, "licence_policy": licence_policy.version()},
                    "why": choice["reasons"],
                }
                shots.append(shot)
                scene_shots.append(shot["shot_id"])
                previous = dict(shot, part_id=scene["part_id"])
                at += length
        seconds = round(tl["duration"] / tl["fps"], 2)
        scene_rows.append({"scene_id": scene["scene_id"], "part_id": scene["part_id"], "beat_ids": scene["beat_ids"],
                           "shot_ids": scene_shots, "seconds": seconds, "start": round(scene_start, 2)})
        scene_start += seconds
    total = round(sum(s["seconds"] for s in shots), 2)
    band_name, band = pace_band(family, levels)
    changes_before = len(visual_changes(shots))
    moves_added = pace_pass(shots, band)
    split = level_split(shots, levels)
    main_level = max(split, key=lambda lvl: (split[lvl]["seconds"], level_rank(lvl, levels))) if split else ""
    l3_plus = round(sum(v["seconds"] for lvl, v in split.items() if level_rank(lvl, levels) >= level_rank("L3", levels)) / total, 4) if total else 0.0
    out = {
        "schema": SCHEMA, "version": VERSION, "video_id": video.get("video_id"), "title": video.get("title", ""),
        "level_profile": profile, "subject_family": family, "levels_version": levels["version"], "grammar_version": grammar["version"],
        "benchmark_version": load_benchmark()["version"], "capabilities_version": toolbox.capabilities_version,
        "world": world, "scenes": scene_rows, "shots": shots, "seconds": total, "beats": len(beats),
        "level_split": split, "main_level": main_level, "l3_plus_share": l3_plus,
        "pace": pace_report(shots, band_name, band, before=changes_before, added=moves_added),
        "cuts": sum(1 for s in shots if s["camera"] == "cut"), "first_use": first_use,
        "wording": {"version": soul.load_wording()["version"], "hits": soul.wording_hits(beats)},
        "assets": {"procedural_capabilities": sorted({s["capability"] for s in shots if s["assets"]["procedural"]}),
                   "sources": sorted({src for s in shots for src in s["assets"]["sources"]}),
                   "not_for_lessons": sorted({h["tool"] for s in shots for h in s["assets"]["not_for_lessons"]}),
                   "licence_policy": licence_policy.version()},
    }
    blocking, advisory = check_video(out, beats, levels=levels, toolbox=toolbox)
    out["checks"] = {"blocking": blocking, "advisory": advisory}
    out["render_allowed"] = not blocking
    out["rule_table"] = rule_table(out, grammar)
    return out


def level_split(shots: list, levels: dict | None = None) -> dict:
    levels = levels or load_levels()
    total = sum(s["seconds"] for s in shots) or 1.0
    split = {}
    for lvl in [l["id"] for l in levels["levels"]]:
        mine = [s for s in shots if s["level"] == lvl]
        if mine:
            seconds = round(sum(s["seconds"] for s in mine), 2)
            split[lvl] = {"shots": len(mine), "seconds": seconds, "share": round(seconds / total, 4)}
    for s in shots:
        if s["level"] not in split:
            split.setdefault(s["level"], {"shots": 0, "seconds": 0.0, "share": 0.0})
            split[s["level"]]["shots"] += 1
            split[s["level"]]["seconds"] = round(split[s["level"]]["seconds"] + s["seconds"], 2)
            split[s["level"]]["share"] = round(split[s["level"]]["seconds"] / total, 4)
    return split


# ---------------------------------------------------------------- the checks

def check_video(plan: dict, beats: list, *, levels: dict | None = None, toolbox=None) -> tuple:
    """(blocking, advisory) for one video's shot list. Blocking: a level outside the ladder (L1, L5b: a planning error), W-01,
    said ≠ shown (B-03), a sentence without its shot (B-01), an unknown block. Advisory: the pace (VG-01, the visual-change
    rate against its band), an L2 shot without its reason, the benchmark's slots (B-02, B-04 to B-07, B-09), the cuts.
    No video is blocked because of its level (Navin, 26 October 2026)."""
    from ..toolbox import registry as registry_module
    levels = levels or load_levels()
    toolbox = toolbox or registry_module.load()
    blocking, advisory = [], []
    allowed = set(levels["shot_levels"])
    known_blocks = {b for cap in toolbox.capabilities.values() for b in cap.blocks} | set(registry_module.grammar_blocks())
    shots = plan.get("shots") or []
    # B-01: one sentence, one shot, in order.
    expected = [(b["beat_id"], k + 1) for b in beats for k in range(len(split_sentences(b.get("say", ""))))]
    got = [(s["beat_id"], int(s["shot_id"].rsplit(".", 1)[1])) for s in shots]
    if got != expected:
        missing = [f"{b}.{k}" for b, k in expected if (b, k) not in set(got)]
        blocking.append(f"B-01: {len(expected)} spoken sentences but {len(got)} shots in that order" +
                        (f"; no shot for {', '.join(missing[:8])}" if missing else ""))
    for s in shots:
        sid = s["shot_id"]
        if s["level"] not in allowed:
            blocking.append(f"shot {sid}: level {s['level']!r} is outside BIE's output (allowed: {', '.join(levels['shot_levels'])}); "
                            "a plan that asks for it is a planning error (visual_levels.json)")
        if not s.get("block"):
            blocking.append(f"shot {sid}: no block")
        for b in s.get("blocks") or []:
            if b not in known_blocks:
                blocking.append(f"shot {sid}: unknown block {b!r} (capabilities.json names the blocks)")
        said = _lower(s["sentence"])
        for label in s.get("labels") or []:
            if label.lower() not in said:
                blocking.append(f"shot {sid}: label {label!r} is not said in its sentence; nothing on screen the sentence does not name (B-03)")
        if not s.get("labels") and s.get("capability") not in ("board_build", "mnemonic_card") and english_terms(s["sentence"]):
            names = [t for t in english_terms(s["sentence"]) if t in STRUCTURE_WORDS]
            if names:
                blocking.append(f"shot {sid}: the sentence names {names[0]!r} but the shot labels nothing (B-03)")
        if s["seconds"] > MICRO_PACE_SECONDS and s.get("capability") not in ("board_build", "mnemonic_card"):
            advisory.append(f"shot {sid}: {s['seconds']} s for one sentence; the benchmark gives a shot 3-5 s (B-01): a long sentence "
                            "could be two")
        if s.get("motion") if "motion" in s else _has(s["sentence"], MOTION_WORDS):
            if not any(b in ("particle_flow", "flow_arrows", "camera_path") for b in s["blocks"]) and s["capability"] not in ("board_build", "mnemonic_card", "split_compare"):
                advisory.append(f"shot {sid}: a function or process sentence without motion (B-04, VG-08)")
        if s.get("first_use") and "yaani" not in (s.get("markers") or []) and not s.get("opened_in_beat"):
            advisory.append(f"shot {sid}: first use of {', '.join(s['first_use'][:3])} without 'yaani' or an example in its beat (B-05): the "
                            "caption shows the term; the plain meaning should be spoken at once")
        organ = _has(s["sentence"], ORGAN_WORDS)
        if organ and _has(s["sentence"], WHERE_WORDS) and s["capability"] != "organ_zoom":
            advisory.append(f"shot {sid}: 'where found' ({organ[0]}) without a zoom from the organ (B-09)")
        if s["purpose"] == "recap" and not s.get("question") and s["capability"] not in ("board_build", "mnemonic_card"):
            advisory.append(f"shot {sid}: a recap not on the board that fills (B-07)")
        if _has(s["sentence"], NAME_WORDS) and "concept_arrow" not in s["blocks"] and s["capability"] not in ("board_build", "mnemonic_card", "split_compare"):
            advisory.append(f"shot {sid}: a name without its reason shown as A → B (B-06)")
    for s in shots:
        if s["level"] == "L2" and not s.get("level_reason"):
            advisory.append(f"shot {s['shot_id']}: L2 without its reason; L2 only where a flat drawing shows the point better, with the reason "
                            "on the shot (Navin, 26 October 2026)")
    pace = plan.get("pace") or {}
    if shots and pace.get("target_seconds") and pace.get("within_target") is False:
        low, high = pace["target_seconds"]
        advisory.append(f"video: one visual change every {pace['seconds_per_change']} s; the {pace['band']} pace is {low:g}-{high:g} s per change (VG-01)")
    for hit in (plan.get("wording") or {}).get("hits") or []:
        blocking.append(f"beat {hit['beat_id']}: \"{hit['sentence'][:80]}\" points at the book ({hit['words']!r}) (W-01)")
    cuts = sum(1 for s in shots if s["camera"] == "cut")
    if shots and cuts > max(1, len(shots) // 10):
        advisory.append(f"video: {cuts} cuts in {len(shots)} shots; cuts are rare, the camera moves to the next part (VG-01)")
    # B-02: seconds per family member.
    per_member = {}
    for s in shots:
        if s.get("member"):
            per_member[s["member"]] = round(per_member.get(s["member"], 0.0) + s["seconds"], 2)
    for m, sec in per_member.items():
        if not MEMBER_SECONDS[0] <= sec <= MEMBER_SECONDS[1]:
            advisory.append(f"member {m}: {sec} s across its shots; the benchmark gives about 40-50 s per member (B-02)")
    plan["per_member_seconds"] = per_member
    return blocking, advisory


RULE_NOTES = {
    "B-01": "one sentence, one shot", "B-02": "seconds per member", "B-03": "said = shown (labels)", "B-04": "function → motion",
    "B-05": "first use → yaani", "B-06": "name → reason (A → B)", "B-07": "recap on the board", "B-08": "kinetic captions on top",
    "B-09": "where found → organ zoom", "B-10": "focus glow", "B-11": "one dark style", "B-12": "depth from the level profile",
}


def rule_table(plan: dict, grammar: dict | None = None) -> list:
    """The 25-rule table (12 benchmark + 11 grammar + W-01 + LOOK-01) for a shot list: pass, partial, fail or n/a, with the shots
    concerned. A plan-level reading; Part B reads the rendered frames against the same rules."""
    grammar = grammar or load_grammar()
    bench = load_benchmark()
    shots = plan.get("shots") or []
    blocking = plan.get("checks", {}).get("blocking") or []
    advisory = plan.get("checks", {}).get("advisory") or []
    rows = []

    def status(rule, *, fail_when=False, partial_when=False, na=False, note="", shots_ids=()):
        state = "n/a" if na else "fail" if fail_when else "partial" if partial_when else "pass"
        rows.append({"rule": rule, "status": state, "note": note, "shots": list(shots_ids)[:12]})

    def hits(prefix):
        return [p for p in blocking + advisory if f"({prefix})" in p or p.startswith(prefix)]

    n = len(shots)
    b01 = hits("B-01")
    avg = round(sum(s["seconds"] for s in shots) / n, 1) if n else 0
    status("B-01", fail_when=any(p.startswith("B-01") for p in blocking), partial_when=bool(b01),
           note=f"{n} shots for {n} clauses, {avg} s each on average (3-5 s)" + (f"; {len(b01)} over {MICRO_PACE_SECONDS:g} s" if b01 else ""))
    status("B-02", partial_when=bool(hits("B-02")), note="; ".join(f"{m} {s} s" for m, s in (plan.get("per_member_seconds") or {}).items()) or "no family member named",
           na=not plan.get("per_member_seconds"))
    status("B-03", fail_when=bool([p for p in blocking if "(B-03)" in p]), note=f"{sum(1 for s in shots if s['labels'])} of {n} shots label a named object")
    motion_shots = [s["shot_id"] for s in shots if "particle_flow" in s["blocks"] or "flow_arrows" in s["blocks"]]
    status("B-04", partial_when=bool(hits("B-04")), note=f"{len(motion_shots)} motion shots", shots_ids=motion_shots)
    yaani = [s["shot_id"] for s in shots if "yaani" in s["markers"]]
    status("B-05", partial_when=bool(hits("B-05")), note=f"{len(yaani)} yaani shots; {len(hits('B-05'))} first uses without yaani", shots_ids=yaani)
    arrows = [s["shot_id"] for s in shots if "concept_arrow" in s["blocks"]]
    status("B-06", partial_when=bool(hits("B-06")), note=f"{len(arrows)} reason arrows", shots_ids=arrows)
    boards = [s["shot_id"] for s in shots if s["capability"] == "board_build"]
    status("B-07", partial_when=bool(hits("B-07")), note=f"{len(boards)} board shots", shots_ids=boards)
    status("B-08", note="every shot carries the kinetic caption with its English terms", fail_when=any("kinetic_caption" not in s["blocks"] for s in shots))
    zooms = [s["shot_id"] for s in shots if s["capability"] == "organ_zoom"]
    status("B-09", partial_when=bool(hits("B-09")), note=f"{len(zooms)} organ zooms", shots_ids=zooms)
    glows = [s["shot_id"] for s in shots if "focus_glow" in s["blocks"]]
    status("B-10", note=f"{len(glows)} shots light one structure", shots_ids=glows)
    status("B-11", note="one dark style, one accent per member: decided by the render (Part B)", partial_when=True)
    status("B-12", note=f"level profile {plan.get('level_profile', {}).get('id')}; grammar the same for every level")
    cuts = plan.get("cuts", 0)
    pace = plan.get("pace") or {}
    band = pace.get("target_seconds")
    status("VG-01", partial_when=bool(hits("VG-01")),
           note=f"{len(plan.get('scenes') or [])} scenes, {cuts} cuts; one visual change every {pace.get('seconds_per_change', 0)} s"
                + (f" ({pace.get('band')} pace {band[0]:g}-{band[1]:g} s)" if band else " (no pace target for this subject yet)")
                + (f"; {pace.get('camera_moves_added', 0)} camera moves added by the director, {pace.get('seconds_per_change_before', 0)} s before" if pace.get("camera_moves_added") else ""))
    status("VG-02", note="labels are code text with a leader line (leader_label on every shot)", fail_when=any("leader_label" not in s["blocks"] for s in shots))
    cut_shots = [s["shot_id"] for s in shots if "cutaway" in s["blocks"] or "exploded_view" in s["blocks"]]
    status("VG-03", na=not cut_shots and not any(_has(s["sentence"], INSIDE_WORDS) for s in shots), note=f"{len(cut_shots)} cutaway shots", shots_ids=cut_shots)
    scale = [s["shot_id"] for s in shots if "scale_compare" in s["blocks"]]
    status("VG-04", na=not scale, note=f"{len(scale)} scale comparisons", shots_ids=scale)
    status("VG-05", na=not any("equation_steps" in s["blocks"] for s in shots), note="no equation in this video")
    status("VG-06", na=not any("graph_plot" in s["blocks"] or "function_graph" in s["blocks"] for s in shots), note="no graph in this video")
    splits = [s["shot_id"] for s in shots if "split_compare" in s["blocks"]]
    status("VG-07", na=not splits and not any(s["purpose"] == "compare" for s in shots), note=f"{len(splits)} split screens", shots_ids=splits)
    status("VG-08", partial_when=bool(hits("VG-08")), note=f"{len(motion_shots)} shots move", shots_ids=motion_shots)
    status("VG-09", note="one dark background, one accent per concept: decided by the render (Part B)", partial_when=True)
    status("VG-10", na=not any(b in ("timeline", "timeline_build", "india_map") for s in shots for b in s["blocks"]), note="no history or map shot")
    status("VG-11", na=True, note="no character in this topic and level")
    w = (plan.get("wording") or {}).get("hits") or []
    status("W-01", fail_when=bool(w), note=f"{len(w)} sentences point at the book" if w else "no sentence points at the book",
           shots_ids=[f"{h['beat_id']}" for h in w])
    status("LOOK-01", partial_when=True, note="decided after the render: the look check scores 3 frames per route against 3 benchmark "
                                             "frames on six axes (bie/brain/look.py); advice only, Navin's eye decides")
    ids = {r["id"] for r in bench["rules"]} | {r["id"] for r in grammar["rules"]}
    return [r for r in rows if r["rule"] in ids]


# ---------------------------------------------------------------- the AI director's shape, the run, the pages

def to_director_video(plan: dict, beats: list) -> dict:
    """The shot list as the Section 3 director's video (scenes with elements, camera and actions tied to spoken words),
    so ``visual.run_visual`` and ``to_scene_spec`` consume it unchanged."""
    says = {b["beat_id"]: b["say"] for b in beats}
    scenes = []
    for scene in plan["scenes"]:
        shots = [s for s in plan["shots"] if s["scene_id"] == scene["scene_id"]]
        elements, camera, actions = [], [], []
        seen = set()
        for s in shots:
            cue_word = next((w for w in WORD.findall(s["sentence"]) if len(w) > 2), s["sentence"].split()[0])
            if s["block"] not in seen:
                seen.add(s["block"])
                elements.append({"element_id": s["block"], "kind": "cell_or_micro" if s["level"] == "L5a" else "diagram",
                                 "shows": s["sentence"][:120], "parts_to_label": s["labels"], "detail": "schematic",
                                 "source_item_ids": s["items"]})
            camera.append({"cue": {"beat_id": s["beat_id"], "word": cue_word}, "move": s["camera"], "target_element_id": s["block"],
                           "note": "; ".join(s["why"])[:120]})
            actions.append({"cue": {"beat_id": s["beat_id"], "word": cue_word}, "element_id": s["block"],
                            "action": "flow" if "particle_flow" in s["blocks"] else "highlight", "detail": ", ".join(s["labels"])[:120]})
        scenes.append({"scene_id": scene["scene_id"], "beat_ids": scene["beat_ids"],
                       "frame": {"process": "", "how_it_works": "", "when_or_sequence": "", "conditions_or_atmosphere": "", "who_or_what_changes": ""},
                       "style": "one dark world, one accent per member", "setting": plan["world"]["capability"],
                       "elements": elements, "camera": camera, "actions": actions, "visual_math": [],
                       "interaction": {"type": "none", "question_id": "", "prompt": "", "target_element_id": ""}})
    return {"video_id": plan["video_id"], "title": plan.get("title", ""), "status": "passed" if plan.get("render_allowed") else "failed",
            "scenes": scenes, "says": says}


def run_shots(chapter: dict, lesson: dict, course, out_dir, *, video_ids=None, toolbox=None, voice: dict | None = None) -> dict:
    """Shot lists for every passed script of a lesson (or ``video_ids``): shots/<video>.json, SHOTS.md and the summary."""
    out = Path(out_dir)
    (out / "shots").mkdir(parents=True, exist_ok=True)
    wanted = set(video_ids or ())
    summary = {"schema": "bie.brain.shots-run/1", "course": chapter.get("course"), "videos": [], "levels_version": load_levels()["version"],
               "grammar_version": load_grammar()["version"]}
    plans = []
    for video in lesson.get("videos") or []:
        if wanted and video["video_id"] not in wanted:
            continue
        if video.get("status") != "passed" or not video.get("beats"):
            summary["videos"].append({"video_id": video["video_id"], "status": "skipped", "why": "the script did not pass"})
            continue
        plan = build_video(video, chapter, course, toolbox=toolbox, voice=(voice or {}).get(video["video_id"]))
        (out / "shots" / f"{video['video_id']}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        plans.append(plan)
        summary["videos"].append({"video_id": plan["video_id"], "status": "render_allowed" if plan["render_allowed"] else "blocked",
                                  "shots": len(plan["shots"]), "seconds": plan["seconds"], "level_split": plan["level_split"],
                                  "main_level": plan["main_level"], "l3_plus_share": plan["l3_plus_share"], "pace": plan["pace"],
                                  "blocking": plan["checks"]["blocking"], "advisory": len(plan["checks"]["advisory"]),
                                  "wording_hits": len(plan["wording"]["hits"])})
    summary["chapter"] = chapter_report(plans)
    (out / "SHOTS.md").write_text(render_markdown(plans, summary), encoding="utf-8")
    (out / "shots.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def chapter_report(plans: list, levels: dict | None = None) -> dict:
    """Star A (Navin, 26 October 2026): of the chapter's (or book's) videos, how many have their main level at L3 or above;
    the target is 90-99 %, a target to work towards, never a blocker; below it, the video's name and the reason."""
    levels = levels or load_levels()
    target = levels["targets"]["chapter"]
    floor = level_rank(target["at_or_above"], levels)
    rows, by_level = [], {}
    for plan in plans:
        split = plan["level_split"]
        top = max(split, key=lambda lvl: split[lvl]["seconds"]) if split else ""
        by_level[plan["main_level"]] = by_level.get(plan["main_level"], 0) + 1
        caps = {}
        for s in plan["shots"]:
            if s["level"] == plan["main_level"]:
                caps[s["capability"]] = caps.get(s["capability"], 0) + s["seconds"]
        lead = max(caps, key=caps.get) if caps else ""
        rows.append({"video_id": plan["video_id"], "main_level": plan["main_level"], "l3_plus_share": plan["l3_plus_share"],
                     "below": level_rank(plan["main_level"], levels) < floor,
                     "reason": f"main level {plan['main_level']}: {split.get(top, {}).get('share', 0):.0%} of its seconds, mostly {lead} shots"
                     + (f" ({plan['shots'][0]['level_reason']})" if plan["shots"] and plan["shots"][0].get("level_reason") else "")})
    above = sum(1 for r in rows if not r["below"])
    share = round(above / len(rows), 4) if rows else 0.0
    return {"star": "A", "decided": target["decided"], "videos": len(rows), "by_main_level": by_level, "l3_plus_videos": above,
            "share": share, "target": list(target["target"]), "meets_target": bool(rows) and share >= target["target"][0],
            "below_target": [r for r in rows if r["below"]], "rows": rows, "blocker": False}


def render_markdown(plans: list, summary: dict | None = None) -> str:
    lines = ["# Shot lists (Task 046 · the code director)", ""]
    if summary:
        lines.append(f"Visual levels {summary.get('levels_version')} · visual grammar {summary.get('grammar_version')} · "
                     "one spoken sentence = one shot (B-01, 3-5 s) · the level rule has two stars (Navin, 26 October 2026): A, the "
                     "chapter target, 90-99 % of videos with their main level at L3 or above (a target, never a blocker); B, the level "
                     "is per shot, from the content; no video is blocked because of its level.")
        lines.append("")
        chapter = summary.get("chapter")
        if chapter:
            lines += ["## Chapter report (star A)", "", "| Video | Main level | L3+ share of seconds | Visual change every | Camera moves added | W-01 | Render |",
                      "| --- | --- | --- | --- | --- | --- | --- |"]
            by_id = {p["video_id"]: p for p in plans}
            for r in chapter["rows"]:
                p = by_id[r["video_id"]]
                lines.append(f"| {r['video_id']} | {r['main_level']} | {r['l3_plus_share']:.1%} | {p['pace']['seconds_per_change']} s | "
                             f"{p['pace']['camera_moves_added']} | {len(p['wording']['hits'])} | {'allowed' if p['render_allowed'] else 'blocked'} |")
            lines += ["", f"Videos with main level L3 or above: **{chapter['l3_plus_videos']} of {chapter['videos']} ({chapter['share']:.0%})**; "
                      f"target {chapter['target'][0]:.0%}-{chapter['target'][1]:.0%} → " + ("met" if chapter["meets_target"] else "not met") + "."]
            for r in chapter["below_target"]:
                lines.append(f"- {r['video_id']}: {r['reason']}")
            lines.append("")
    for plan in plans:
        lines += [f"## {plan['video_id']} · {plan['title']}", "",
                  f"- World: `{plan['world']['capability']}` ({plan['world']['block']}, {plan['world']['level']}); level profile "
                  f"{plan['level_profile'].get('id')}; {len(plan['scenes'])} scenes, {len(plan['shots'])} shots, {plan['seconds']} s "
                  f"({round(plan['seconds'] / 60, 1)} min); cuts {plan['cuts']}.",
                  f"- Main level **{plan['main_level']}**; level mix: " + ", ".join(f"{lvl} {v['shots']} shots / {v['seconds']} s ({v['share']:.1%})" for lvl, v in plan["level_split"].items())
                  + f"; L3 or above {plan['l3_plus_share']:.1%} of the seconds → " + ("**render allowed**" if plan["render_allowed"] else "**not rendered** (see blocking)") + ".",
                  f"- Pace (VG-01): one visual change every **{plan['pace']['seconds_per_change']} s** ({plan['pace']['changes']} changes"
                  + (f"; {plan['pace']['band']} target {plan['pace']['target_seconds'][0]:g}-{plan['pace']['target_seconds'][1]:g} s" if plan['pace']['target_seconds'] else "; no target for this subject yet")
                  + (f"; {plan['pace']['seconds_per_change_before']} s before the director added {plan['pace']['camera_moves_added']} camera moves" if plan['pace']['camera_moves_added'] else "") + ").",
                  f"- W-01: {len(plan['wording']['hits'])} sentences point at the book" + (":" if plan["wording"]["hits"] else "."), ""]
        for h in plan["wording"]["hits"]:
            lines.append(f"  - beat {h['beat_id']}: \"{h['sentence']}\" ← `{h['words']}` ({h['group']})")
        if plan["wording"]["hits"]:
            lines.append("")
        if plan["checks"]["blocking"]:
            lines += ["**Blocking:**", ""] + [f"- {p}" for p in plan["checks"]["blocking"]] + [""]
        if plan["checks"]["advisory"]:
            lines += [f"**Advisory ({len(plan['checks']['advisory'])}):**", ""] + [f"- {p}" for p in plan["checks"]["advisory"][:40]]
            if len(plan["checks"]["advisory"]) > 40:
                lines.append(f"- … and {len(plan['checks']['advisory']) - 40} more in shots/{plan['video_id']}.json")
            lines.append("")
        lines += [f"### The {len(plan.get('rule_table') or [])} rules", "", "| Rule | Status | Note | Shots |", "| --- | --- | --- | --- |"]
        for r in plan["rule_table"]:
            lines.append(f"| {r['rule']} | {r['status']} | {r['note']} | {', '.join(r['shots'][:6])} |")
        lines += ["", "### Shots", "", "| # | t | s | Level | Capability · blocks | Camera | Labels | Sentence |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for s in plan["shots"]:
            lines.append(f"| {s['shot_id']} | {int(s['start'] // 60)}:{int(s['start'] % 60):02d} | {s['seconds']} | {s['level']} | "
                         f"{s['capability']} · {', '.join(s['blocks'])} | {s['camera']} | {', '.join(s['labels'])} | {s['sentence']} |")
        lines.append("")
    return "\n".join(lines)
