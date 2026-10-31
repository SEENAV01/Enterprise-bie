"""World plan → scene spec for the L3 ``world_scene`` block (Task 046 Part C, from the economy kit of 27 October 2026).

Same contract as the canvas plans (``bie/brain/canvas.py``): the director names props, people, effects and camera moves,
each on a cue word ([beat_id, word] or [beat_id, "", fraction]); this code turns cues into frames through
``timing.py`` and checks the plan (unknown kinds, cue words not in their beat, camera keys out of order, a crowd step
that is not a number, the picture staying still too long). This is Navin's "C" level: a part that tells a story with
actors in a place is shown inside a small designed world; the kits a world can draw are listed in ``KITS`` (a part whose
place has no kit falls back to the canvas, and the place goes to the missing-capability log). Kits so far: the shop street
(PR 1) and the bank (PR 3, for the Money chapter's v1: a worker saves ₹500 in an account, a borrower pays an EMI): a bank
building with a teller behind its counter, customers who walk in and out (the ``crowd``), and a ``board`` whose value
changes on cue (a passbook balance, an EMI due) with the old value struck out.
"""
from __future__ import annotations

import copy

from .. import canvas
from .. import formats
from ..canvas import PlanError
from . import timing

KINDS = {"shop", "price_tag", "crowd", "coin_rain", "balance", "label", "pull_arrow", "title", "lamp", "foreground", "shopkeeper",
         "bank", "teller", "board"}
# The places a story part can be set in (Navin, 27 October 2026: "a shop and its buyers, a bank and its borrowers, a factory
# and its workers, a port, a farm"), with the words that name them in a Hinglish script. A place with a kit in ``KITS`` goes
# to world mode (C); a place without one falls back to the canvas (B) and goes to the missing-capability log (Part C, PR 3
# builds the kits the chosen video needs). The director (bie/brain/canvas_director.py) decides; this module only draws.
PLACES = {
    # A tea stall, a market stall and the English "bazaar" are shops too (the Money chapter's v1, 28 October 2026).
    "shop": ("दुकान", "दुकानदार", "shop", "shopkeeper", "बाज़ार", "बाजार", "bazaar", "bazar", "market", "खरीदार", "buyer", "buyers", "ग्राहक",
             "customer", "customers", "किराना", "mandi", "मंडी", "tea stall", "stall", "stalls", "ठेला", "ठेले", "चायवाला", "चायवाले", "चाय"),
    # The bank's own words: accounts, deposits, savings, passbooks, instalments, the teller (never the English "account" alone:
    # money's "unit of account" is a shop story in v1).
    "bank": ("बैंक", "bank", "banks", "कर्ज़", "कर्ज", "loan", "loans", "borrower", "borrowers", "depositor", "depositors", "जमा", "उधार", "rbi",
             "खाता", "खाते", "passbook", "पासबुक", "savings", "बचत", "instalment", "installment", "किश्त", "क़िस्त", "teller", "cashier"),
    "factory": ("फैक्ट्री", "फ़ैक्ट्री", "factory", "factories", "कारखाना", "कारखाने", "मज़दूर", "मजदूर", "worker", "workers", "मशीन", "machine"),
    "port": ("बंदरगाह", "port", "ports", "ship", "ships", "जहाज़", "जहाज", "export", "exports", "import", "imports", "निर्यात", "आयात", "container"),
    "farm": ("खेत", "किसान", "farm", "farmer", "farmers", "फसल", "crop", "crops", "harvest", "कटाई", "tractor", "बीज"),
    # Navin's places for the real-world application (27 October 2026) add the petrol pump; a mandi and a kirana shop are shops.
    "petrol_pump": ("petrol pump", "पेट्रोल पंप", "पेट्रोल पम्प", "fuel station", "petrol", "diesel", "पेट्रोल", "डीज़ल", "डीजल"),
}
PLACE_LABELS = {"shop": "shop", "bank": "bank", "factory": "factory", "port": "port", "farm": "farm", "petrol_pump": "petrol pump"}
KITS = {"shop": {"label": "a shop with buyers on a street", "words": PLACES["shop"]},
        "bank": {"label": "a bank with its customers at the counter", "words": PLACES["bank"]}}
# The element kind that is a kit's place: a world plan for that kit must contain one (the other kinds dress the street).
PLACE_KINDS = {"shop": "shop", "bank": "bank"}
CUE_KEYS = ("cue", "until_cue", "tilt_cue")
# What a board, a price tag and the title can hold (the Money chapter's v1, 28 October 2026: the director wrote sentences into
# boards, 63 of 98 values over 16 characters, and they ran out of the box). A board holds up to BOARD_LINES lines of
# BOARD_CHARS characters (its own line breaks first, then long lines wrapped at spaces by code); a price tag shows a price;
# the title stays short. Longer text is refused with the limit named, so the maker says it in the narration or a label.
BOARD_LINES, BOARD_CHARS, TAG_CHARS, TITLE_CHARS = 2, 28, 9, 30      # 28 since 31 October 2026 (Task 046 Part D1): a board holds a name or a short
# phrase, never a sentence (Navin, 30 October: "sirf text hi text screen par dikha to video ... ek book ban jaayegi"); 40 on 29 October had let
# whole sentences sit on boards.


def wrap_value(text: str, width: int = BOARD_CHARS) -> list:
    """A board's value as lines: the maker's own line breaks are kept, a longer line is wrapped at its spaces."""
    out = []
    for line in str(text or "").split("\n"):
        cur = ""
        for word in line.split(" "):
            if not cur:
                cur = word
            elif len(cur) + 1 + len(word) <= width:
                cur += " " + word
            else:
                out.append(cur)
                cur = word
        out.append(cur)
    return out


def _check_text(n: dict) -> None:
    """The text limits of a board, a price tag and the title (PlanError names the limit and what to do instead)."""
    kind, nid = n.get("kind"), n.get("id", "?")
    if kind == "board":
        for st in n.get("steps") or []:
            lines = wrap_value(st.get("text", ""))
            if len(lines) > BOARD_LINES or any(len(line) > BOARD_CHARS for line in lines):
                raise PlanError(f"{nid}: a board holds at most {BOARD_LINES} lines of {BOARD_CHARS} characters, and "
                                f"'{str(st.get('text', ''))[:40]}' needs {len(lines)} lines: say the rest in the narration, or split it "
                                "over two steps on two cue words")
            st["lines"] = lines
    elif kind == "price_tag":
        for st in n.get("steps") or []:
            if len(str(st.get("text", ""))) > TAG_CHARS:
                raise PlanError(f"{nid}: a price tag shows a price ('₹65', '₹10,000'; at most {TAG_CHARS} characters), not "
                                f"'{str(st.get('text', ''))[:30]}': use a board for words")
    elif kind == "title" and len(str(n.get("text", ""))) > TITLE_CHARS:
        raise PlanError(f"{nid}: the title is at most {TITLE_CHARS} characters ('{str(n.get('text', ''))[:40]}' has "
                        f"{len(str(n.get('text', '')))})")


def compile_world(plan: dict, *, voice: dict | None = None, lead_in: float = timing.LEAD_IN, kit: str = ""):
    """(scene, report) for a world plan; ``kit`` (or ``plan["kit"]``) names the kit the plan was written for, so a bank story
    is refused until it has its bank (a shop drawn for a bank story is the wrong world)."""
    kit = kit or plan.get("kit") or ""
    beats = plan["beats"]
    if not beats:
        raise PlanError("a world plan needs at least one beat")
    says = {b["beat_id"]: b["say"] for b in beats}
    sid = plan.get("id", "world")
    voice = voice if voice is not None else formats.voice_of(beats)      # Task 047: the spoken words, once the voice section writes them
    tl = timing.build(beats, [{"scene_id": sid, "beat_ids": [b["beat_id"] for b in beats]}], voice=voice, lead_in=lead_in)
    fps = tl[sid]["fps"]

    def frame_of(cue):
        return canvas.cue_frame(tl, sid, says, cue)

    changes = []
    els = []
    for n in copy.deepcopy(plan.get("elements") or []):
        if n.get("kind") not in KINDS:
            raise PlanError(f"{n.get('id', '?')}: unknown world element kind {n.get('kind')!r} (kinds: {', '.join(sorted(KINDS))})")
        _check_text(n)
        if "cue" in n:
            n["at"] = frame_of(n.pop("cue")); changes.append(n["at"])
        if "until_cue" in n:
            n["until"] = frame_of(n.pop("until_cue")); changes.append(n["until"])
        if "tilt_cue" in n:
            n["tilt_at"] = frame_of(n.pop("tilt_cue")); changes.append(n["tilt_at"])
        for key in ("steps", "packets"):
            for st in n.get(key, []):
                st["at"] = frame_of(st.pop("cue")); changes.append(st["at"])
                if "n" in st and (isinstance(st["n"], bool) or not isinstance(st["n"], int) or st["n"] < 0):
                    raise PlanError(f"{n['id']}: a step count must be a whole number")
        for key in ("lift", "carry"):
            if key in n:
                n[key]["at"] = frame_of(n[key].pop("cue")); changes.append(n[key]["at"])
        els.append(n)
    kinds = {e["kind"] for e in els}
    places = [k for k, kind in PLACE_KINDS.items() if kind in kinds]
    if kit and PLACE_KINDS.get(kit) not in kinds:
        raise PlanError(f"a world in {place_label(kit)} needs its place: add a {PLACE_KINDS.get(kit, kit)} element")
    if not places:
        raise PlanError("a world needs its place: add a " + " or a ".join(PLACE_KINDS.values()) + " element (the kits so far)")
    cam = []
    for k in plan.get("camera") or []:
        f = frame_of(k["cue"])
        if cam and f < cam[-1]["at"]:
            raise PlanError("camera keys must be in time order")
        cam.append({"at": f, "x": k["x"], "y": k.get("y", 540), "zoom": k.get("zoom", 1.0), "frames": k.get("frames", 36)})
        changes.append(f)
    if not cam:
        raise PlanError("a world needs at least one camera key")
    duration = tl[sid]["duration"]
    pts = sorted(set(changes)) + [duration]
    still = max(b - a for a, b in zip(pts, pts[1:])) / fps
    problems = [f"the picture stays the same for {still:.1f} s (limit {canvas.MAX_STILL_S:.0f} s)"] if still > canvas.MAX_STILL_S else []
    data = {"world_width": plan.get("world_width", 5200), "elements": els, "camera": cam}
    scene = {"id": sid, "duration": duration, "camera": [{"at": 0}], "captions": canvas.captions_of(tl, sid, beats),
             "layers": [{"id": sid + "_world", "type": "block", "block": "world_scene", "at": 0, "box": {"x": 0, "y": 0, "w": 1, "h": 1}, "data": data}]}
    report = {"scene": sid, "seconds": round(duration / fps, 1), "elements": len(els), "camera_moves": len(cam),
              "longest_still_s": round(still, 1), "change_every_s": round(duration / fps / max(1, len(pts) - 1), 1), "problems": problems,
              "mode": "C", "level": "L3", "kit": kit or places[0]}
    return scene, report


def place_of(text: str) -> str:
    """The place a part's words name (the place named most often wins), or "" for a part that is not a story in a place."""
    low = text.lower()
    counts = {place: sum(low.count(w.lower()) for w in words) for place, words in PLACES.items()}
    best = max(counts, key=counts.get)
    return best if counts[best] else ""


def kit_for(text: str) -> str:
    """The world kit for a part's place, or "" when the place has no kit yet (or the part has no place)."""
    place = place_of(text)
    return place if place in KITS else ""


def place_label(place: str) -> str:
    """The words of a place for a report or the missing-capability log ("petrol_pump" → "petrol pump")."""
    return PLACE_LABELS.get(place, place.replace("_", " "))
