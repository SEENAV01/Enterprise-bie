"""Aggregate the teaching cards (teach/<ID>.json) into the numbers behind BIE's narration, talmel, game and notes rules.

    python3 teach_aggregate.py OUT.json

Talmel lag is measured by code: for every tile whose card names the spoken word that names what appeared, the word's
time is taken from the speech-to-text word timings (stt2/<ID>.json, nearest occurrence to the change) and
lag = change time - word time (positive = the picture came after the word).
"""
import collections
import json
import os
import re
import sys

B = os.path.dirname(os.path.abspath(__file__))


def norm(w):
    return re.sub(r"[\[\]\.,!?;:'\"।()]", "", str(w)).strip().lower()


def main(out):
    moves, ex_kinds, lead, rel, mech, shapes, open_moves, close_moves = (collections.Counter() for _ in range(8))
    concept_types = collections.Counter()
    lags, lags_by_rel = [], collections.defaultdict(list)
    breakdown, orders, checks, talmel_sum, best, weak = [], [], [], [], [], []
    story_gaps, games, questions = [], [], []
    vids = 0
    for f in sorted(os.listdir(os.path.join(B, "teach"))):
        if not f.endswith(".json"):
            continue
        c = json.load(open(os.path.join(B, "teach", f)))
        vid = c["id"]
        vids += 1
        words = []
        sp = os.path.join(B, "stt2", vid + ".json")
        if os.path.exists(sp):
            words = [(w[0], norm(w[2])) for s in json.load(open(sp))["segments"] for w in (s.get("words") or [])]
        bu = c.get("book_understanding", {})
        for k in bu.get("concepts", []):
            concept_types[k.get("type", "?")] += 1
        breakdown.append({"video": vid, "rule": bu.get("breakdown_rule", "")})
        orders.append({"video": vid, "order": bu.get("teaching_order", "")})
        n = c.get("narration", {})
        open_moves[(n.get("opening") or {}).get("move", "?")] += 1
        close_moves[(n.get("closing") or {}).get("move", "?")] += 1
        for m in n.get("moves", []):
            moves[m.get("move", "?")] += 1
        for e in n.get("examples", []):
            ex_kinds[e.get("kind", "?")] += 1
        for sb in n.get("story_before_term", []):
            try:
                story_gaps.append(float(sb["t_term"]) - float(sb["t_story"]))
            except (KeyError, TypeError, ValueError):
                pass
        for t in c.get("talmel", []):
            lead[t.get("lead", "?")] += 1
            rel[t.get("relation", "?")] += 1
            nw = norm(t.get("naming_word", ""))
            if nw and words:
                tc = float(t.get("t_shown", 0))
                hits = [wt for wt, w in words if w == nw and abs(wt - tc) <= 6]
                if hits:
                    wt = min(hits, key=lambda x: abs(x - tc))
                    lag = round(tc - wt, 2)
                    lags.append(lag)
                    lags_by_rel[t.get("relation", "?")].append(lag)
        talmel_sum.append({"video": vid, "summary": c.get("talmel_summary", "")})
        for g in c.get("game_ideas", []):
            mech[g.get("mechanic", "?")] += 1
            games.append({"video": vid, **g})
        for q in c.get("notes_questions", []):
            shapes[q.get("answer_shape", "?")] += 1
            questions.append({"video": vid, **q})
        checks += [{"video": vid, "check": x} for x in c.get("checks_learned", [])]
        best += [{"video": vid, **x} for x in c.get("teaching_best", [])]
        weak += [{"video": vid, **x} for x in c.get("teaching_weak", [])]

    def pct(xs, p):
        xs = sorted(xs)
        return round(xs[min(len(xs) - 1, int(p * len(xs)))], 2) if xs else None

    tot = sum(rel.values()) or 1
    res = {
        "videos": vids,
        "concept_types": dict(concept_types.most_common()),
        "opening_moves": dict(open_moves.most_common()), "closing_moves": dict(close_moves.most_common()),
        "moves": dict(moves.most_common()), "example_kinds": dict(ex_kinds.most_common()),
        "story_before_term_gap_s": {"n": len(story_gaps), "median": pct(story_gaps, 0.5), "p90": pct(story_gaps, 0.9)},
        "talmel": {"tiles": tot, "lead": dict(lead.most_common()), "relation": dict(rel.most_common()),
                   "meaning_shown_share": round(rel.get("shows_the_step", 0) / tot, 2),
                   "words_only_share": round((rel.get("names_the_term", 0) + rel.get("repeats_speech_as_text", 0)) / tot, 2),
                   "lag_s": {"n": len(lags), "median": pct(lags, 0.5), "p10": pct(lags, 0.1), "p90": pct(lags, 0.9),
                             "within_1s": round(sum(abs(x) <= 1 for x in lags) / max(1, len(lags)), 2)},
                   "lag_by_relation": {k: {"n": len(v), "median": pct(v, 0.5)} for k, v in lags_by_rel.items()}},
        "game_mechanics": dict(mech.most_common()), "notes_answer_shapes": dict(shapes.most_common()),
        "breakdown_rules": breakdown, "teaching_orders": orders, "talmel_summaries": talmel_sum,
        "checks_learned": checks, "games": games, "notes_questions": questions, "best": best, "weak": weak,
    }
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print("videos", vids, "| concept types", dict(concept_types.most_common(6)))
    print("opening", dict(open_moves.most_common(5)), "| closing", dict(close_moves.most_common(5)))
    print("moves", dict(moves.most_common(14)))
    print("examples", dict(ex_kinds.most_common()), "| story->term gap", res["story_before_term_gap_s"])
    print("talmel", res["talmel"]["lead"], res["talmel"]["relation"])
    print("lag", res["talmel"]["lag_s"], {k: v for k, v in res["talmel"]["lag_by_relation"].items()})
    print("games", dict(mech.most_common()), "| notes", dict(shapes.most_common()), "| checks", len(checks), "| questions", len(questions))


if __name__ == "__main__":
    main(sys.argv[1])
