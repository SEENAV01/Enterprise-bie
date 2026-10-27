"""Aggregate the economy canvas cards into a needs list, and say for each need whether BIE has it.

    python econ_aggregate.py CARDS_DIR OUT.json

"bie_main" is what BIE's main branch could draw on 27 Oct 2026 (bie/brain/video/blocks: core layers and toolbox
blocks); "econ_kit" is what this kit adds (blocks/canvas_build.tsx, blocks/curve_story.tsx, tools/econ_canvas.py).
"""
import collections
import json
import os
import sys

STATUS = {
    # kind: (bie_main, econ_kit, note)
    "icon": ("partial", "yes", "main has image layers but no icon library; kit adds a 4,200-icon CC BY index and icon elements"),
    "crowd": ("no", "yes", "repeated icons that grow/shrink with the story"),
    "text_box": ("partial", "yes", "main labels are dark-theme pills; kit adds boxes/notes that fit-check their text"),
    "tag": ("partial", "yes", "coloured pill chips"),
    "title_text": ("yes", "yes", ""),
    "arrow": ("yes", "yes", "kit arrows attach to element sides, elbow or curve, draw on"),
    "flow_chain": ("partial", "yes", "main has flow_build/mermaid; kit lays a chain on the grid with cues per step"),
    "tree": ("partial", "yes", "main has tree_build (dark); kit lays a root + children tree by code with elbow connectors, each child on its word"),
    "bullet_chain": ("partial", "partial", "main steps layer; kit: boxes + down arrows by plan"),
    "graph": ("partial", "yes", "main function_graph/xy_lines draw curves; kit curve_story adds walking dot, drops, shades, guides, shifts"),
    "bar_or_chart": ("yes", "yes", "Chart.js / Vega / Plotly blocks"),
    "table": ("partial", "yes", "kit table: rows appear on their words, cells/columns light up; fit-checked"),
    "timeline": ("yes", "partial", "main timeline/timeline_build; arcs between points missing"),
    "value_change": ("no", "yes", "number struck out and replaced, with up/down arrow"),
    "mark": ("no", "yes", "tick / cross drawn on"),
    "up_down_arrow": ("no", "yes", "part of value_change"),
    "callout": ("partial", "yes", "note box whose phrases light up when spoken"),
    "highlight": ("partial", "yes", "box / dashed / band, drawn on"),
    "formula": ("yes", "partial", "main equation_steps (KaTeX); kit has no formula element of its own"),
    "map": ("yes", "no", "main india_map / world_points"),
    "character": ("no", "no", "BIE needs an ORIGINAL presenter character (never a caricature of a real person)"),
    "photo": ("n/a", "n/a", "photos of real people are never used: BIE uses a name card or a silhouette instead"),
    "logo_or_brand": ("n/a", "n/a", "logos and emblems are never used: BIE uses a generic icon"),
    "question_mark": ("yes", "yes", "question layer / icon"),
    "end_screen": ("n/a", "n/a", "channel promotion, ignored"),
}


def main(cards_dir, out):
    kinds = collections.Counter()
    kinds_videos = collections.defaultdict(set)
    motions = collections.Counter()
    layouts = collections.Counter()
    canvas = collections.Counter()
    levels = collections.Counter()
    seg_seconds = []
    notes = []
    for f in sorted(os.listdir(cards_dir)):
        if not f.endswith(".json"):
            continue
        c = json.load(open(os.path.join(cards_dir, f)))
        vid = c.get("id", f[:-5])
        for s in c.get("segments", []):
            if any(e.get("kind") == "end_screen" for e in s.get("elements", [])):
                continue
            seg_seconds.append(float(s.get("end", 0)) - float(s.get("start", 0)))
            for e in s.get("elements", []):
                kinds[e["kind"]] += 1
                kinds_videos[e["kind"]].add(vid)
            for m in s.get("motions", []):
                motions[m] += 1
            layouts[s.get("layout", "?")] += 1
            canvas[s.get("canvas", "?")] += 1
            levels[s.get("level", "?")] += 1
            if s.get("notes"):
                notes.append(f"{vid} {s.get('start')}-{s.get('end')}: {s['notes']}")
    rows = []
    for k, n in kinds.most_common():
        st = STATUS.get(k, ("?", "?", "new kind"))
        rows.append({"kind": k, "segments": n, "videos": len(kinds_videos[k]), "bie_main": st[0], "econ_kit": st[1], "note": st[2]})
    seg_seconds.sort()
    res = {"videos": len([f for f in os.listdir(cards_dir) if f.endswith('.json')]), "segments": len(seg_seconds),
           "segment_seconds_median": seg_seconds[len(seg_seconds) // 2] if seg_seconds else None,
           "levels": dict(levels), "layouts": dict(layouts.most_common()), "canvas_moves": dict(canvas.most_common()),
           "motions": dict(motions.most_common()), "elements": rows, "notes": notes}
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in res.items() if k not in ("notes", "elements")}, indent=1))
    for r in rows:
        print(f"{r['kind']:14s} seg {r['segments']:4d}  videos {r['videos']:2d}  main {r['bie_main']:8s} kit {r['econ_kit']:8s} {r['note']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
