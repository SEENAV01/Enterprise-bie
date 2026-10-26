"""From the code director's shot list to a VideoSpec the block library renders (Task 046, Part B).

``video_spec(plan, beats, ...)`` turns ``bie/brain/shots.py``'s plan into the choreography data of ``blocks/index.tsx``:
one scene per script part (VG-01), with

- one ``cell_sheet`` world layer for the whole scene whose ``data.shots`` carry every clause's flags (member, the lit part,
  the particle flow, the camera move, cutaway or exploded view, the leader labels, the organ to zoom from), so the
  benchmark blocks ``particle_flow``, ``focus_glow``, ``organ_zoom``, ``leader_label``, ``camera_path``, ``cutaway`` and
  ``exploded_view`` act inside one canvas and one camera, never a cut;
- a ``kinetic_caption`` per clause on top (B-08) with its English terms;
- the L3 panels where the director chose them: ``board_build`` (one board per scene that fills, B-07), ``mnemonic_card``,
  ``split_compare`` (two members side by side, VG-07), ``concept_arrow`` (name → reason, B-06), ``tree_build`` (the family
  overview), ``scale_compare`` (VG-04);
- a closing credits scene from the licence gate (BIE's own models and the placeholder voice carry no outside licence).

Timing is the plan's (``timing.build``, with the real voice durations when a voice was made first). ``segment(plan, parts)``
keeps the scenes of the named parts (the epithelium family part for the benchmark render). ``shot_frames`` gives every
shot's absolute frame range for the rule table. ``check_spec`` is the said = shown check on the finished spec: every label
in a shot's world is said in that shot's clause.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .. import shots as shots_module
from . import timing

SCHEMA = "bie.brain.video-spec/1"
W, H = 1920, 1080
FULL = {"x": 0, "y": 0, "w": 1, "h": 1}
CAPTION_BOX = {"x": 0, "y": 0, "w": 1, "h": 0.2}
BOARD_BOX = {"x": 0.655, "y": 0.5, "w": 0.33, "h": 0.46}
PANEL_BOX = {"x": 0.02, "y": 0.17, "w": 0.96, "h": 0.8}

MEMBER_ID = {"simple squamous": "simple_squamous", "stratified squamous": "stratified_squamous", "simple cuboidal": "simple_cuboidal",
             "stratified cuboidal": "stratified_cuboidal", "simple columnar": "simple_columnar", "stratified columnar": "stratified_columnar",
             "pseudostratified": "pseudostratified", "transitional": "transitional", "keratinised": "keratinised", "ciliated": "ciliated",
             "glandular": "glandular"}
MEMBER_WORDS = {"simple_squamous": "Simple squamous", "stratified_squamous": "Stratified squamous", "simple_cuboidal": "Simple cuboidal",
                "stratified_cuboidal": "Stratified cuboidal", "simple_columnar": "Simple columnar", "stratified_columnar": "Stratified columnar",
                "pseudostratified": "Pseudostratified", "transitional": "Transitional", "keratinised": "Keratinised", "ciliated": "Ciliated",
                "glandular": "Glandular"}
DEFAULT_MEMBER = "generic"

FOCUS = (("nucleus", ("nucleus", "nuclei")), ("basement_membrane", ("basement membrane", "basement", "membrane", "आधार", "base")),
         ("cilia", ("cilia", "ciliated", "cilium")), ("microvilli", ("microvilli", "microvillus", "projections")),
         ("keratin", ("keratin", "keratinised", "keratinized")), ("junction", ("junction", "junctions", "cementing", "intercellular", "जोड़", "gaps", "gap")),
         ("duct", ("duct", "ducts", "gland", "glands", "glandular", "secrete")), ("layers", ("layers", "layer", "stratified", "तह", "तहों", "तहें", "stack")),
         ("tissue", ("underlying tissue", "tissue", "connective")), ("top", ("surface", "ऊपर", "top", "apical", "free surface")),
         ("cell", ("cell", "cells", "sheet", "sheets", "tiles", "tile", "cubes", "cube", "pillars", "pillar", "चादर", "परत", "पासे", "covering", "lining", "epithelium", "epithelial")))
FLOW = (("absorb", ("absorb", "absorption", "सोख", "अंदर लेना", "वापस लेने", "अंदर आती")), ("secrete", ("secrete", "secretion", "secretes", "छोड़", "droplet")),
        ("cross", ("diffuse", "diffusion", "exchange", "पार", "cross", "gases", "pass", "passes")),
        ("sweep", ("sweep", "mucus", "हिल", "आगे", "move", "movement", "ले जा", "directional", "cilia")),
        ("shed", ("shed", "shedding", "झड़", "renew", "renewal", "flake")))
ORGAN = (("lung", ("lung", "lungs", "alveol", "air sac", "air sacs", "trachea", "respiratory", "airway", "फेफड़")),
         ("kidney", ("kidney", "tubule", "tubules", "bowman", "nephron", "गुर्द")),
         ("intestine", ("intestine", "intestines", "gut", "digestive", "आँत", "stomach", "oesophagus", "esophagus")),
         ("skin", ("skin", "epidermis", "त्वचा", "mouth", "मुँह", "vagina")),
         ("bladder", ("bladder", "ureter", "urethra", "urinary", "urine")),
         ("gland", ("gland", "glands", "duct", "ducts", "salivary", "mammary", "sweat", "लार")))
SPLIT_AT = re.compile(r";\s*|\s+(?:जबकि|लेकिन|versus|vs\.?)\s+", re.IGNORECASE)
YAANI = re.compile(r"(यानी|यानि|मतलब|अर्थात|yaani|yani|matlab)", re.IGNORECASE)


def _first(table, text: str, default: str = "") -> str:
    low = (text or "").lower()
    for key, words in table:
        if any(w in low for w in words):
            return key
    return default


def member_of(shot: dict, carried: str) -> str:
    low = shot["sentence"].lower()
    named_all = [mid for key, mid in MEMBER_ID.items() if key in low]
    if len(named_all) >= 2:                                   # a family overview names several: the world stays as it is
        return carried
    named = shots_module.member_of(shot["sentence"])
    if named and named in MEMBER_ID:
        return MEMBER_ID[named]
    if shot.get("member") and shot["member"] in MEMBER_ID:
        return MEMBER_ID[shot["member"]]
    return carried


def focus_of(shot: dict) -> str | list:
    for label in shot.get("labels") or []:
        part = _first(FOCUS, label)
        if part:
            return part
    part = _first(FOCUS, shot["sentence"])
    return part or "cell"


def label_parts(shot: dict, focus: str) -> list:
    out, seen = [], set()
    for label in (shot.get("labels") or [])[:3]:
        part = _first(FOCUS, label) or focus
        if part in seen:
            continue
        seen.add(part)
        out.append({"text": label, "part": part})
    return out


def world_shot(shot: dict, member: str, scene_start_frame: int) -> dict:
    blocks = set(shot.get("blocks") or [])
    entry = {"at": shot["frames"][0], "until": shot["frames"][0] + shot["frames"][1], "member": member}
    focus = focus_of(shot)
    if shot["capability"] in ("board_build", "mnemonic_card", "tree_hierarchy", "split_compare"):
        entry["focus"] = []                                        # the world rests while the panel teaches
        entry["dim"] = shot["capability"] != "board_build"
    else:
        entry["focus"] = focus
    entry["camera"] = {"move": shot.get("camera", "hold")}
    if "particle_flow" in blocks or shot["capability"] == "particle_flow":
        kind = _first(FLOW, shot["sentence"], "cross")
        entry["flow"] = {"kind": kind, "particles": 36 if kind != "sweep" else 26, "seconds": 2.4}
    if "cutaway" in blocks:
        entry["cutaway"] = True
    if "exploded_view" in blocks:
        entry["exploded"] = True
    if member == "transitional" and re.search(r"stretch|फैल|flatter|चपटी", shot["sentence"], re.IGNORECASE):
        entry["stretch"] = True
    if shot["capability"] == "organ_zoom" or "organ_zoom" in blocks:
        entry["organ"] = _first(ORGAN, shot["sentence"], "lung")
        entry["camera"] = {"move": "zoom_in"}
    entry["labels"] = label_parts(shot, entry["focus"] if isinstance(entry["focus"], str) else "cell")
    return entry


def caption_layer(shot: dict, accent: str) -> dict:
    cap = shot.get("caption") or {}
    return {"id": f"cap-{shot['shot_id']}", "type": "block", "block": "kinetic_caption", "at": shot["frames"][0],
            "until": shot["frames"][0] + shot["frames"][1], "box": CAPTION_BOX,
            "data": {"text": cap.get("text") or shot["sentence"], "terms": cap.get("terms") or [], "accent": accent}}


def _short(text: str, limit: int = 46) -> str:
    text = re.sub(r"\s+", " ", text).strip(" ।.;:,")
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _lines(text: str, limit: int = 4) -> list:
    pieces = [p.strip(" ।.;,") for p in re.split(r"[;।,]\s*|\s+और\s+|\s+फिर\s+", text) if p.strip(" ।.;,")]
    return pieces[:limit] or [_short(text, 60)]


def panel_layers(shot: dict, member: str, accent: str, boards: dict, scene_duration: int) -> list:
    """The L3 panels of one shot (none for a plain world shot)."""
    at, length = shot["frames"]
    until = at + length
    layers = []
    cap = shot["capability"]
    sentence = shot["sentence"]
    if cap == "board_build":
        board = boards.setdefault("board", {"id": "board", "type": "block", "block": "board_build", "at": at, "until": scene_duration,
                                            "box": BOARD_BOX, "data": {"title": "shape → job", "compact": True, "rows": []}})
        a = MEMBER_WORDS.get(member, "") if shots_module.member_of(sentence) else (shot.get("labels") or [_short(sentence, 18)])[0]
        rest = re.sub(r"^[^:：]*[:：]\s*", "", sentence) if ":" in sentence else sentence
        board["data"]["rows"].append({"a": _short(a, 22), "b": _short(rest, 34), "at": at, "accent": accent})
    elif cap == "mnemonic_card":
        head, _, tail = sentence.partition(":")
        layers.append({"id": f"card-{shot['shot_id']}", "type": "block", "block": "mnemonic_card", "at": at, "until": until, "box": FULL,
                       "data": {"title": _short(head if tail else "याद रखो", 40), "lines": _lines(tail or sentence), "accent": accent}})
    elif cap == "split_compare":
        halves = [h for h in SPLIT_AT.split(sentence) if h and h.strip()]
        named = []
        for key, mid in MEMBER_ID.items():
            if key in sentence.lower() and mid not in named:
                named.append(mid)
        left_member = named[0] if named else member
        right_member = named[1] if len(named) > 1 else None
        left = {"title": MEMBER_WORDS.get(left_member, "A"), "member": left_member, "lines": _lines(halves[0] if halves else sentence, 2)}
        right = {"title": MEMBER_WORDS.get(right_member, "B") if right_member else _short(halves[1], 24) if len(halves) > 1 else "दूसरा",
                 "lines": _lines(halves[1] if len(halves) > 1 else "", 2) if len(halves) > 1 else []}
        if right_member:
            right["member"] = right_member
        layers.append({"id": f"split-{shot['shot_id']}", "type": "block", "block": "split_compare", "at": at, "until": until, "box": PANEL_BOX,
                       "data": {"left": left, "right": right, "slots": []}})
    elif cap == "tree_hierarchy":
        layers.append({"id": f"tree-{shot['shot_id']}", "type": "block", "block": "tree_build", "at": at, "until": until, "box": PANEL_BOX,
                       "data": {"root": {"name": "Epithelium", "children": [
                           {"name": "Simple · 1 layer", "children": [{"name": "Squamous"}, {"name": "Cuboidal"}, {"name": "Columnar"}]},
                           {"name": "Stratified · कई layers", "children": [{"name": "Squamous"}, {"name": "Cuboidal"}, {"name": "Columnar"}]},
                           {"name": "Special", "children": [{"name": "Keratinised"}, {"name": "Transitional"}, {"name": "Pseudo stratified"}]}]},
                                "wrap": 10, "seconds": max(2.0, length / timing.FPS * 0.8)}})
    if "concept_arrow" in (shot.get("blocks") or []) and cap not in ("board_build", "mnemonic_card", "split_compare", "tree_hierarchy"):
        m = YAANI.search(sentence)
        if m:
            before, after = sentence[:m.start()], sentence[m.end():]
            frm = (re.findall(r"[A-Za-z][A-Za-z\-]+", before) or [_short(before, 16)])[-1]
            to = _short(after, 30)
            reason = ""
        else:
            labels = shot.get("labels") or []
            frm = labels[0] if labels else _short(sentence, 16)
            to = labels[1] if len(labels) > 1 else ""
            reason = _short(sentence, 60) if not to else ""
        if to:
            box = {"x": 0, "y": 0.2, "w": 0.64 if "board" in boards else 1, "h": 0.8}
            layers.append({"id": f"arrow-{shot['shot_id']}", "type": "block", "block": "concept_arrow", "at": at, "until": until, "box": box,
                           "data": {"from": frm, "to": to, "reason": reason, "accent": accent}})
    if "scale_compare" in (shot.get("blocks") or []):
        nums = re.findall(r"(\d[\d.,]*)\s*(µm|um|nm|mm|cm|MB|GB|%|गुना|times)", sentence)
        if nums:
            items = [{"label": f"{v} {u}", "value": float(v.replace(",", "")), "unit": u} for v, u in nums[:3]]
            layers.append({"id": f"scale-{shot['shot_id']}", "type": "block", "block": "scale_compare", "at": at, "until": until,
                           "box": {"x": 0.55, "y": 0.2, "w": 0.43, "h": 0.5}, "data": {"items": items, "accent": accent}})
    return layers


ACCENTS_PATH = Path(__file__).resolve().parent / "blocks" / "toolbox" / "accents.json"


def accent_of(member: str) -> str:
    """One accent per member (VG-09), from the same file the blocks read."""
    accents = json.loads(ACCENTS_PATH.read_text(encoding="utf-8"))
    return accents.get(member, accents.get("generic", "#38d3c3"))


def scene_spec(plan: dict, scene: dict, *, carried_member: str) -> tuple:
    """(scene spec, last member) for one of the plan's scenes."""
    shots = [s for s in plan["shots"] if s["scene_id"] == scene["scene_id"]]
    duration = int(round(scene["seconds"] * timing.FPS))
    world_shots, layers, boards = [], [], {}
    member = carried_member
    for shot in shots:
        member = member_of(shot, member)
        accent = accent_of(member)
        world_shots.append(world_shot(shot, member, 0))
        layers.append(caption_layer(shot, accent))
        layers += panel_layers(shot, member, accent, boards, duration)
    world = {"id": "world", "type": "block", "block": "cell_sheet", "at": 0, "box": FULL,
             "data": {"member": world_shots[0]["member"] if world_shots else member, "shots": world_shots}}
    all_layers = [world] + list(boards.values()) + layers
    return ({"id": scene["scene_id"], "duration": duration, "layers": all_layers, "camera": [{"at": 0, "box": FULL}]}, member)


def credits_scene(credits: list, voice: dict | None, seconds: float = 4.0) -> dict:
    lines = ["Models, drawings and motion: BIE's own code (route A three.js; route C Blender glTF)"]
    lines += [f"{c.get('title', c.get('asset_id', ''))}: {c.get('author', '')} · {c.get('licence', '')}" for c in credits]
    lines.append("Voice: " + ((voice or {}).get("provider") or "silent timeline with captions") + " (placeholder; Task 047 brings the real voice)")
    frames = int(seconds * timing.FPS)
    return {"id": "credits", "duration": frames, "camera": [{"at": 0, "box": FULL}], "layers": [
        {"id": "credits-steps", "type": "steps", "at": 0, "box": {"x": 0.08, "y": 0.12, "w": 0.84, "h": 0.76}, "title": "Credits",
         "steps": [{"label": _short(l, 90), "at": 6 + i * 10} for i, l in enumerate(lines)]}]}


def segment(plan: dict, parts: list | None = None, scene_ids: list | None = None) -> dict:
    """The plan reduced to the scenes of the named parts (or scene ids); frames inside a scene are unchanged."""
    keep = [s for s in plan["scenes"] if (parts and s["part_id"] in parts) or (scene_ids and s["scene_id"] in scene_ids)]
    ids = {s["scene_id"] for s in keep}
    return dict(plan, scenes=keep, shots=[s for s in plan["shots"] if s["scene_id"] in ids])


def video_spec(plan: dict, *, voice: dict | None = None, audio: str | None = None, credits: list | None = None, with_credits: bool = True) -> dict:
    scenes, member = [], DEFAULT_MEMBER
    for scene in plan["scenes"]:
        spec, member = scene_spec(plan, scene, carried_member=member)
        scenes.append(spec)
    if with_credits:
        scenes.append(credits_scene(credits or [], voice))
    out = {"schema": SCHEMA, "fps": timing.FPS, "width": W, "height": H, "captions": False, "scenes": scenes,
           "video_id": plan.get("video_id"), "title": plan.get("title", ""), "levels_version": plan.get("levels_version"),
           "grammar_version": plan.get("grammar_version")}
    if audio:
        out["audio"] = audio
    return out


def shot_frames(plan: dict, spec: dict) -> list:
    """Every shot's absolute frame range in the finished video (scenes one after another), for the rule table."""
    starts, cursor = {}, 0
    for scene in spec["scenes"]:
        starts[scene["id"]] = cursor
        cursor += scene["duration"]
    rows = []
    for s in plan["shots"]:
        base = starts.get(s["scene_id"], 0)
        rows.append({"shot_id": s["shot_id"], "scene_id": s["scene_id"], "from": base + s["frames"][0], "to": base + s["frames"][0] + s["frames"][1],
                     "seconds": s["seconds"], "level": s["level"], "capability": s["capability"], "camera": s["camera"], "labels": s["labels"],
                     "sentence": s["sentence"]})
    return rows


def check_spec(plan: dict, spec: dict) -> list:
    """Said = shown on the finished spec (B-03): every world label and every caption of a shot comes from that shot's
    clause; every clause has its caption; the world layer covers the whole scene."""
    problems = []
    by_id = {s["shot_id"]: s for s in plan["shots"]}
    for scene in spec["scenes"]:
        if scene["id"] == "credits":
            continue
        world = next((l for l in scene["layers"] if l["id"] == "world"), None)
        if not world:
            problems.append(f"scene {scene['id']}: no world layer")
            continue
        if world["at"] != 0 or world.get("until") not in (None, scene["duration"]):
            problems.append(f"scene {scene['id']}: the world layer does not cover the whole scene (VG-01)")
        plan_shots = [s for s in plan["shots"] if s["scene_id"] == scene["id"]]
        for ws, ps in zip(world["data"]["shots"], plan_shots):
            said = ps["sentence"].lower()
            for label in ws.get("labels") or []:
                if label["text"].lower() not in said:
                    problems.append(f"shot {ps['shot_id']}: world label {label['text']!r} is not said (B-03)")
        caps = {l["id"] for l in scene["layers"] if l.get("block") == "kinetic_caption"}
        for ps in plan_shots:
            if f"cap-{ps['shot_id']}" not in caps:
                problems.append(f"shot {ps['shot_id']}: no kinetic caption (B-08)")
        if len(world["data"]["shots"]) != len(plan_shots):
            problems.append(f"scene {scene['id']}: {len(world['data']['shots'])} world shots for {len(plan_shots)} clauses (B-01)")
    return problems


def write(spec: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    return out
