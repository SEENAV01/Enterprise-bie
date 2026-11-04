"""Aggregate batch-3 canvas cards (all videos, v3 fields) into the numbers behind the economy show-lexicon.

    python3 aggregate3.py CARDS3_DIR OUT.json

Counts per idea_type (segments, seconds, meaning_carrier mix, top things and actions), things and actions ranked by
segments and videos, camera moves, on-screen words, and the best/weak moments. Synonymous thing names are merged by
ALIAS so different card writers count as one saancha.
"""
import collections
import json
import os
import sys

ALIAS = {
    "bank": "bank_building", "commercial_bank": "bank_building", "bank_icon": "bank_building", "banks": "bank_building",
    "central_bank": "rbi_building", "rbi": "rbi_building", "reserve_bank": "rbi_building", "rbi_icon": "rbi_building",
    "people": "crowd_people", "crowd": "crowd_people", "persons": "crowd_people",
    "man": "person", "woman": "person", "customer": "person", "depositor": "person", "borrower": "person",
    "person_borrower": "person", "person_depositor": "person", "investor": "person", "worker": "person",
    "money_bag": "money_bag", "moneybag": "money_bag", "cash": "cash_stack", "cash_bundle": "cash_stack",
    "currency_note": "rupee_note", "banknote": "rupee_note", "note": "rupee_note", "notes": "rupee_note",
    "coins": "coin", "gold": "gold_bar", "gold_bars": "gold_bar",
    "bond": "bond_certificate", "bonds": "bond_certificate", "certificate": "bond_certificate",
    "govt_building": "government_building", "government": "government_building", "parliament": "government_building",
    "india": "india_map", "india_silhouette": "india_map", "map_india": "india_map",
    "world": "globe", "earth": "globe", "world_globe": "globe",
    "law": "law_document", "act_document": "law_document", "law_book": "law_document", "law_icon": "law_document",
    "graph": "graph_axes", "chart": "bar_chart", "bar_graph": "bar_chart",
    "safe": "vault", "locker": "vault", "safe_vault": "vault",
    "timeline_bar": "timeline", "timeline_line": "timeline", "era_band": "timeline",
    "small_safe": "vault", "phone": "mobile_phone", "person_investor": "person", "sleepless_investor": "person",
    "office_worker": "person", "industrial_worker": "person", "farm_labourer": "person", "rural_labourer": "person",
    "shopping_cart": "basket", "shopping_bag": "basket", "cart": "basket", "banknote": "rupee_note",
    "licence_certificate": "licence_paper", "cds_document": "document", "stamp_seal": "stamp",
    "real_person_caricature": "real_person_photo", "real_hand_footage": "live_footage",
    "office_building": "office_building", "stock_exchange": "stock_exchange_building", "exchange_building": "stock_exchange_building",
    "share": "share_certificate", "shares": "share_certificate", "segmented_bar": "stacked_bar", "range_bar": "stacked_bar",
    "piggy": "piggy_bank", "measuring_tape": "ruler", "national_flag": "india_flag", "line_chart_icon": "bar_chart_icon",
    "sign_badge": "percentage_badge", "tax_badge": "percentage_badge", "currency_symbol": "dollar_note",
    "percent": "percentage_badge", "percentage": "percentage_badge", "percent_sign": "percentage_badge",
}


def norm(t):
    t = str(t).strip().lower().replace(" ", "_").replace("-", "_")
    return ALIAS.get(t, t)


def main(cards_dir, out):
    by_type = collections.defaultdict(lambda: {"segments": 0, "seconds": 0.0, "carrier": collections.Counter(),
                                               "things": collections.Counter(), "actions": collections.Counter(),
                                               "videos": set(), "examples": []})
    things, things_v = collections.Counter(), collections.defaultdict(set)
    actions, actions_v = collections.Counter(), collections.defaultdict(set)
    carrier, camera, formats = collections.Counter(), collections.Counter(), collections.Counter()
    words, best, weak = [], [], []
    places, place_changes = collections.Counter(), []
    n_vid = n_seg = 0
    for f in sorted(os.listdir(cards_dir)):
        if not f.endswith(".json"):
            continue
        c = json.load(open(os.path.join(cards_dir, f)))
        vid = c.get("id", f[:-5])
        n_vid += 1
        formats[c.get("format", "?")] += 1
        for m in c.get("best_moments", []):
            best.append({"video": vid, **m})
        for m in c.get("weak_moments", []):
            weak.append({"video": vid, **m})
        for s in c.get("segments", []):
            if s.get("idea_type") == "end_screen" or any(e.get("kind") == "end_screen" for e in s.get("elements", [])):
                continue
            n_seg += 1
            it = s.get("idea_type", "?")
            d = by_type[it]
            secs = max(0.0, float(s.get("end", 0)) - float(s.get("start", 0)))
            d["segments"] += 1
            d["seconds"] += secs
            d["videos"].add(vid)
            mc = s.get("meaning_carrier", "?")
            d["carrier"][mc] += 1
            carrier[mc] += 1
            camera[s.get("camera", "?")] += 1
            if isinstance(s.get("on_screen_words"), (int, float)):
                words.append(s["on_screen_words"])
            if s.get("place"):                                   # batch 5 on: the world a segment happens in
                places[str(s["place"]).strip().lower()] += 1
                if str(s.get("place_change", "")).strip():
                    place_changes.append({"video": vid, "t": s.get("start"), "place": s["place"], "change": s["place_change"]})
            seg_things = {norm(t) for t in s.get("things", [])}
            for t in seg_things:
                things[t] += 1
                things_v[t].add(vid)
                d["things"][t] += 1
            for a in {str(a).strip().lower() for a in s.get("actions", [])}:
                actions[a] += 1
                actions_v[a].add(vid)
                d["actions"][a] += 1
            d["examples"].append({"video": vid, "t": s.get("start"), "idea": s.get("idea", ""), "shown_as": s.get("shown_as", ""),
                                  "carrier": mc})
    words.sort()
    res = {
        "videos": n_vid, "segments": n_seg, "formats": dict(formats),
        "meaning_carrier": dict(carrier.most_common()), "camera": dict(camera.most_common()),
        "on_screen_words": {"median": words[len(words) // 2] if words else None,
                            "p90": words[int(len(words) * 0.9)] if words else None},
        "idea_types": {k: {"segments": v["segments"], "minutes": round(v["seconds"] / 60, 1), "videos": len(v["videos"]),
                           "meaning_carrier": dict(v["carrier"].most_common()),
                           "top_things": [t for t, _ in v["things"].most_common(12)],
                           "top_actions": [a for a, _ in v["actions"].most_common(10)],
                           "examples": v["examples"]}
                       for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]["segments"])},
        "things": [{"thing": t, "segments": n, "videos": len(things_v[t])} for t, n in things.most_common()],
        "actions": [{"action": a, "segments": n, "videos": len(actions_v[a])} for a, n in actions.most_common()],
        "best_moments": best, "weak_moments": weak,
        "places": dict(places.most_common()), "place_changes": place_changes,
    }
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"videos {n_vid} segments {n_seg} carrier {dict(carrier.most_common())}")
    for k, v in res["idea_types"].items():
        print(f"  {k:14s} seg {v['segments']:3d} min {v['minutes']:5.1f} {v['meaning_carrier']}")
    print("things:", ", ".join(f"{r['thing']} {r['segments']}/{r['videos']}" for r in res["things"][:45]))
    if places:
        print("places:", dict(places.most_common()), "changes:", len(place_changes))
    print("actions:", ", ".join(f"{r['action']} {r['segments']}" for r in res["actions"][:25]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
