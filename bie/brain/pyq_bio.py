"""Fusions and chromosome sets for the PYQ lab (Navin, 19 November 2026): who fuses with whom, and what each part carries.

The maker writes the biology as short lines: the parts (cells, nuclei, gametes, structures) with their chromosome sets,
where they sit, and the fusions. Code adds the sets (n + n = 2n; n + n + n = 3n), keeps the maternal and paternal shares,
counts cells and nuclei separately (7 cells but 8 nuclei in a mature embryo sac), turns sets into chromosome numbers for a
given 2n, and decides which option matches what is asked. Nothing here knows a particular question.

    diploid 24
    entity egg "Egg" cell sets=1 origin=maternal at=50,80
    entity central "Central cell" cell sets=0 nuclei=2 at=50,50
    entity polar1 "Polar nucleus" nucleus sets=1 origin=maternal in=central at=45,50
    entity m1 "Male gamete" gamete sets=1 origin=paternal at=15,95
    fuse syngamy "Syngamy": m1 + egg -> zygote "Zygote" fate="embryo"
    asked sequence 1 2 3
    option 4 = syn1, zygote, pen
"""
from __future__ import annotations

import re
import shlex
from fractions import Fraction

from .pyq_math import match_option, option_numbers

TYPES = ("cell", "nucleus", "gamete", "structure")
ORIGINS = ("maternal", "paternal", "none")
SETS_WORD = {1: "n", 2: "2n", 3: "3n", 4: "4n"}
PLOIDY_WORDS = {"haploid": 1, "diploid": 2, "triploid": 3, "tetraploid": 4}
FUSE = re.compile(r'^\s*fuse\s+([a-z][a-z0-9_]*)\s+"([^"]+)"\s*:\s*(.+?)\s*->\s*([a-z][a-z0-9_]*)\s+"([^"]+)"\s*(.*)$', re.I)


def parse(lines: list) -> tuple:
    spec = {"diploid": None, "entities": {}, "order": [], "fusions": [], "asked": None, "options": {}}
    problems = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        word = line.split()[0].lower()
        try:
            if word == "diploid":
                spec["diploid"] = int(line.split()[1])
                if spec["diploid"] <= 0 or spec["diploid"] % 2:
                    raise ValueError("diploid (2n) must be an even whole number")
            elif word == "entity":
                tokens = shlex.split(line)
                if len(tokens) < 4:
                    raise ValueError('write: entity <id> "<label>" <cell|nucleus|gamete|structure> key=value ...')
                eid, label, kind = tokens[1], tokens[2], tokens[3].lower()
                if kind not in TYPES:
                    raise ValueError(f"type must be one of {', '.join(TYPES)}")
                if eid in spec["entities"]:
                    raise ValueError(f"entity {eid} is defined twice")
                item = {"id": eid, "label": label, "type": kind, "sets": 0, "origin": "none", "in": "", "at": None,
                        "nuclei": None}
                for token in tokens[4:]:
                    key, _, value = token.partition("=")
                    if key == "sets":
                        item["sets"] = int(value)
                    elif key == "origin":
                        if value not in ORIGINS:
                            raise ValueError(f"origin must be one of {', '.join(ORIGINS)}")
                        item["origin"] = value
                    elif key == "in":
                        item["in"] = value
                    elif key == "nuclei":
                        item["nuclei"] = int(value)
                    elif key == "at":
                        x, y = (float(v) for v in value.split(","))
                        if not (0 <= x <= 100 and 0 <= y <= 100):
                            raise ValueError("at=x,y must be in 0..100")
                        item["at"] = [x, y]
                    else:
                        raise ValueError(f"unknown key {key!r} (sets, origin, in, nuclei, at)")
                spec["entities"][eid] = item
                spec["order"].append(eid)
            elif word == "fuse":
                m = FUSE.match(line)
                if not m:
                    raise ValueError('write: fuse <id> "<name>": a + b [+ c] -> <product id> "<product label>" fate="..."')
                inputs = [p.strip() for p in m.group(3).split("+") if p.strip()]
                fate = re.search(r'fate="([^"]*)"', m.group(6) or "")
                spec["fusions"].append({"id": m.group(1), "name": m.group(2), "inputs": inputs, "product": m.group(4),
                                        "label": m.group(5), "fate": fate.group(1) if fate else ""})
            elif word == "asked":
                parts = line.split()[1:]
                if not parts:
                    raise ValueError("asked what? (sequence 1 2 3 | count <id> | sets <id> | ratio <id> | cells | nuclei)")
                spec["asked"] = parts
            elif word == "option":
                m = re.match(r"^\s*option\s+(\d)\s*=\s*(.+)$", line, re.I)
                if not m:
                    raise ValueError("write: option <n> = id, id, id")
                spec["options"][int(m.group(1)) - 1] = [p.strip() for p in m.group(2).split(",") if p.strip()]
            else:
                raise ValueError("lines start with diploid, entity, fuse, asked or option")
        except ValueError as exc:
            problems.append(f"biology line {line!r}: {exc}")
    if not spec["entities"]:
        problems.append("biology: no 'entity' line")
    return spec, problems


def run(lines: list, options: list) -> dict:
    out = {"kind": "fusion", "problems": [], "entities": [], "fusions": [], "counts": {}, "answer_option": None,
           "numbers": set(), "asked_value": None}
    spec, problems = parse(lines)
    out["problems"] += problems
    if problems:
        return out
    ents = {k: dict(v) for k, v in spec["entities"].items()}
    for e in ents.values():
        if e["in"] and e["in"] not in ents:
            out["problems"].append(f"entity {e['id']}: in={e['in']} is not an entity")
        if e["type"] in ("cell", "nucleus", "gamete") and e["at"] is None:
            out["problems"].append(f"entity {e['id']}: give its place with at=x,y")
        e["maternal"] = e["sets"] if e["origin"] == "maternal" else 0
        e["paternal"] = e["sets"] if e["origin"] == "paternal" else 0
    cells = [e for e in ents.values() if e["type"] == "cell"]
    nuclei = 0
    for cell in cells:
        inside = [e for e in ents.values() if e["type"] == "nucleus" and e["in"] == cell["id"]]
        count = len(inside) if inside else (cell["nuclei"] if cell["nuclei"] is not None else (1 if cell["sets"] else 0))
        if cell["nuclei"] is not None and inside and cell["nuclei"] != len(inside):
            out["problems"].append(f"{cell['id']}: nuclei={cell['nuclei']} but {len(inside)} nucleus entities sit in it")
        nuclei += count
    out["counts"] = {"cells": len(cells), "nuclei": nuclei}
    used = set()
    for fusion in spec["fusions"]:
        missing = [i for i in fusion["inputs"] if i not in ents]
        if missing:
            out["problems"].append(f"fusion {fusion['id']}: {', '.join(missing)} not defined")
            continue
        twice = [i for i in fusion["inputs"] if i in used]
        if twice:
            out["problems"].append(f"fusion {fusion['id']}: {', '.join(twice)} already fused once")
        if len(fusion["inputs"]) < 2:
            out["problems"].append(f"fusion {fusion['id']}: a fusion joins at least two parts")
        if fusion["product"] in ents:
            out["problems"].append(f"fusion {fusion['id']}: product id {fusion['product']} is already used")
            continue
        used.update(fusion["inputs"])
        parts = [ents[i] for i in fusion["inputs"]]
        host = next((p for p in parts if p["type"] != "gamete"), parts[0])
        product = {"id": fusion["product"], "label": fusion["label"], "type": "nucleus" if host["type"] == "nucleus" else "cell",
                   "sets": sum(p["sets"] for p in parts), "maternal": sum(p["maternal"] for p in parts),
                   "paternal": sum(p["paternal"] for p in parts), "origin": "none", "in": host["in"],
                   "at": host["at"], "nuclei": None, "made_by": fusion["id"], "fate": fusion["fate"]}
        ents[product["id"]] = product
        out["fusions"].append({**fusion, "sets": product["sets"], "maternal": product["maternal"],
                               "paternal": product["paternal"], "at": product["at"],
                               "sum": " + ".join(SETS_WORD.get(p["sets"], f"{p['sets']}n") for p in parts) + " = " +
                                      SETS_WORD.get(product["sets"], f"{product['sets']}n")})
    half = Fraction(spec["diploid"], 2) if spec["diploid"] else None
    for e in ents.values():
        e["chromosomes"] = int(e["sets"] * half) if half and e["sets"] else None
        e["ploidy"] = SETS_WORD.get(e["sets"], f"{e['sets']}n") if e["sets"] else ""
    out["entities"] = [{k: e[k] for k in ("id", "label", "type", "sets", "ploidy", "maternal", "paternal", "origin", "in",
                                           "at", "chromosomes")} | {"made_by": e.get("made_by", ""), "fate": e.get("fate", "")}
                       for e in ents.values()]
    numbers = {out["counts"]["cells"], out["counts"]["nuclei"]}
    if spec["diploid"]:
        numbers |= {spec["diploid"], spec["diploid"] // 2}
    numbers |= {e["chromosomes"] for e in ents.values() if e["chromosomes"]}
    numbers |= {e["sets"] for e in ents.values()}
    out["numbers"] = numbers
    out["diploid"] = spec["diploid"]
    if spec["asked"]:
        _answer(spec, ents, options or [], out)
    return out


def _sets_in(text: str) -> int | None:
    m = re.search(r"\b([1-4])?\s*n\b", text or "")
    if m:
        return int(m.group(1) or 1)
    for word, sets in PLOIDY_WORDS.items():
        if word in (text or "").lower():
            return sets
    return None


def _answer(spec, ents, options, out):
    asked = spec["asked"]
    kind = asked[0].lower()
    hits = []
    if kind == "sequence":
        want = [int(v) for v in asked[1:]]
        out["asked_value"] = " → ".join(SETS_WORD.get(v, f"{v}n") for v in want)
        for i, ids in spec["options"].items():
            bad = [x for x in ids if x not in ents]
            if bad:
                out["problems"].append(f"option {i + 1}: {', '.join(bad)} not defined")
                continue
            got = [ents[x]["sets"] for x in ids]
            if got == want:
                hits.append(i)
        out["option_sets"] = {i + 1: [ents[x]["ploidy"] for x in ids if x in ents] for i, ids in spec["options"].items()}
    elif kind in ("count", "sets", "ratio") and len(asked) > 1:
        target = ents.get(asked[1])
        if target is None:
            out["problems"].append(f"asked {kind}: {asked[1]} is not an entity or product")
            return
        if kind == "count":
            if target["chromosomes"] is None:
                out["problems"].append("asked count needs 'diploid <2n>'")
                return
            out["asked_value"] = target["chromosomes"]
            m = match_option(target["chromosomes"], options)
            hits = [m] if m is not None else []
        elif kind == "sets":
            out["asked_value"] = target["ploidy"]
            hits = [i for i, text in enumerate(options) if _sets_in(text) == target["sets"]]
        else:
            ratio = f"{target['maternal']}:{target['paternal']}"
            out["asked_value"] = ratio
            hits = [i for i, text in enumerate(options) if re.sub(r"\s", "", text or "").find(ratio) >= 0]
    elif kind in ("cells", "nuclei"):
        out["asked_value"] = out["counts"][kind]
        m = match_option(out["counts"][kind], options)
        hits = [m] if m is not None else []
    else:
        out["problems"].append("asked must be: sequence 1 2 3 | count <id> | sets <id> | ratio <id> | cells | nuclei")
        return
    if len(hits) == 1:
        out["answer_option"] = hits[0]
    elif not hits:
        out["problems"].append(f"no option matches what is asked ({out['asked_value']})")
    else:
        out["problems"].append(f"more than one option matches what is asked ({out['asked_value']}): options "
                               f"{', '.join(str(h + 1) for h in hits)}")
