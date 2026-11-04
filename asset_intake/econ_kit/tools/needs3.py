"""Economy saanche needs list from the 37 cards: every drawn thing ranked by segments, with where BIE gets it.

    python3 needs3.py agg3.json OUT.json

status:
  built_batch3   parametric saancha written in this batch (saanche/econ_saanche.js)
  have_v2        in the Money v2 demo library (draw.js / people.js), parametric
  have_icon      an MIT / CC BY icon is enough (Fluent Emoji, Twemoji, Font Awesome Free; no brands)
  engine         a general engine part, not a subject thing (timeline, table, graph, marks, arrows, panels)
  replace        what the references show is never used by BIE; the replacement is named
  build_next     recurring and still missing: build in the next economy batch
  decision       needs Navin's decision before it is built
  one_off        appears once or twice: left to BIE's AI to make (or an icon) when a book needs it
"""
import json
import sys

STATUS = {
    "brand_logo": ("replace", "institutionBadge (kind + name + sub), never a real logo or emblem"),
    "bank_building": ("have_v2", "bank(label); centralBank for RBI; variants for cooperative / payments / rural branch = build_next"),
    "timeline": ("engine", "timeline part: years, era bands, ownership zones, law arcs, hop arrows (v2 engine has none yet)"),
    "person": ("have_v2", "person rig with 10 looks, poses, expressions"),
    "table_grid": ("engine", "table with rows on their words, highlighted cells (econ_kit canvas_build)"),
    "rupee_note": ("have_v2", "note(value) and noteBundle in BIE's own colours (not RBI designs)"),
    "document": ("built_batch3", "paper(kind=report|contract|...)"),
    "bond_certificate": ("built_batch3", "paper(kind=bond, value, note)"),
    "crowd_people": ("built_batch3", "crowd(n, cols, share, labels, dimRest)"),
    "india_map": ("decision", "India outline must follow the official boundary (Survey of India); open datasets show other boundaries"),
    "graph_axes": ("engine", "curve_story (econ_kit): axes, walking dot, drop lines, shades, shifts"),
    "tick_mark": ("have_v2", "mark(kind=tick)"),
    "law_document": ("built_batch3", "paper(kind=law, title, year, stamp)"),
    "basket": ("have_icon", "Fluent basket / shopping cart; size by spending = build_next variant"),
    "factory": ("have_icon", "Fluent factory; a parametric factory with smoke and goods = build_next"),
    "percentage_badge": ("built_batch3", "disc(text) or institution-free tag"),
    "vault": ("built_batch3", "vault(label, fill, door, locked, tag, metal)"),
    "question_paper": ("one_off", "only in the paper-analysis video; notes/assessment will define its own page saancha"),
    "question_mark": ("have_v2", "mark(kind=question)"),
    "tablet": ("one_off", "channel cut-aways; not needed"),
    "real_person_photo": ("replace", "a name card or a generic person; never a real face"),
    "token_square": ("engine", "coloured unit squares for counting (count/split/join part)"),
    "cross_mark": ("have_v2", "mark(kind=cross)"),
    "committee_desk": ("built_batch3", "committee(n, name, sub, color)"),
    "india_flag": ("one_off", "national flag only where the book needs it, drawn to the Flag Code proportions"),
    "mobile_phone": ("have_v2", "phone(screen=scan|paid|received)"),
    "road_map_blob": ("engine", "lesson road map sidebar whose highlight moves (recap part)"),
    "instrument_sidebar": ("engine", "same as road map sidebar"),
    "globe": ("have_icon", "Fluent globe; a world-to-India flow layout uses the v2 world land outline"),
    "progress_circles": ("one_off", "assessment progress tracker (notes/assessment section)"),
    "shop": ("have_v2", "shop background with counter; a small shop thing = have_icon"),
    "laptop": ("have_icon", "Fluent laptop"),
    "stamp": ("built_batch3", "paper(stamp=...) and disc(text)"),
    "live_footage": ("replace", "never used"),
    "bottle": ("have_icon", "Fluent bottle / goods"),
    "money_bag": ("built_batch3", "moneyBag(w, label, sign)"),
    "dollar_note": ("build_next", "foreign note: note(value, currency) generic, not a real design"),
    "flag_card": ("one_off", "country name card instead of flags"),
    "goods_boxes": ("have_icon", "Fluent package / boxes"),
    "landmark_building": ("replace", "no real landmark buildings; a generic building + place label"),
    "hand": ("build_next", "hands that give / receive / hold (fund surplus → fund scarce); part of the person rig today"),
    "speech_bubble": ("have_v2", "bubble kind2 (engine)"),
    "grocery_bag": ("have_icon", "Fluent shopping bags"),
    "ownership_zone": ("engine", "timeline zone (coloured band over a period with members inside)"),
    "crown": ("have_icon", "Fluent crown (for the colonial-era law sheet)"),
    "stacked_bar": ("engine", "split bar: one sum cut into coloured slices that then travel (split part)"),
    "bank_card": ("have_v2", "accountCard / debit card = have_icon"),
    "focus_circle": ("engine", "highlight / zoom part"),
    "country_flag": ("replace", "country name card"),
    "house": ("have_icon", "Fluent house"),
    "rope": ("build_next", "rope / rod linking two notes (peg): connector style in the engine"),
    "calendar": ("have_v2", "calendar"),
    "licence_paper": ("built_batch3", "paper(kind=licence)"),
    "risk_badge": ("built_batch3", "disc(text=RISK)"),
    "government_building": ("build_next", "generic domed government building (institutionBadge kind=government meanwhile)"),
    "rural_bank_hut": ("build_next", "village bank branch / PACS hut"),
    "stock_exchange_building": ("build_next", "generic exchange building with a ticker band"),
    "oil_barrel": ("have_icon", "Fluent oil drum"),
    "gauge": ("build_next", "rating / risk gauge with a needle"),
    "growth_title_card": ("engine", "title card / heading chip"),
    "sticky_note": ("engine", "note box (canvas_build callout)"),
    "formula_card": ("engine", "formula part (KaTeX equation steps)"),
    "tier_band": ("engine", "nested containers / tier bands (hierarchy part)"),
    "highlight_band": ("engine", "highlight part"),
    "checkbox": ("engine", "tick grid part"),
    "market_banner": ("engine", "heading chip"),
    "money_market_band": ("engine", "labelled ground band that things drop into / rise from"),
    "bar_chart_icon": ("have_icon", "Fluent bar chart"),
    "magnifier": ("have_icon", "Fluent magnifying glass"),
    "warehouse": ("have_icon", "Font Awesome warehouse (CC BY) / Fluent"),
    "car": ("have_icon", "Fluent car"),
    "armchair": ("have_icon", "Fluent chair / couch"),
    "database_cylinder": ("have_icon", "Font Awesome database"),
    "weight_icon": ("have_icon", "Fluent balance scale"),
    "cooperative_bank_badge": ("replace", "institutionBadge(kind=cooperative)"),
    "office_building": ("build_next", "generic office / company building with a name plate"),
    "village_scene": ("have_v2", "village background"),
    "mobile_wallet": ("have_icon", "Fluent mobile phone + purse"),
    "price_tag": ("build_next", "hanging price tag that flips and is struck/replaced (econ_kit world_scene has one in TSX)"),
    "barrier_wall": ("build_next", "wall that blocks a path (arrows loop around it)"),
}


def main(agg, out):
    a = json.load(open(agg))
    rows = []
    for r in a["things"]:
        st, how = STATUS.get(r["thing"], ("one_off", "left to BIE's AI or an icon when a book needs it"))
        if r["segments"] >= 3 and r["thing"] not in STATUS:
            st, how = "build_next", "recurring; check before the next batch"
        rows.append({**r, "status": st, "how": how})
    by = {}
    for r in rows:
        by.setdefault(r["status"], {"things": 0, "segments": 0})
        by[r["status"]]["things"] += 1
        by[r["status"]]["segments"] += r["segments"]
    res = {"schema": "bie.saanche-needs/1", "subject": "economics", "videos": a["videos"], "segments": a["segments"],
           "how_counted": "a thing counts once per card segment it appears in; synonyms merged (aggregate3.ALIAS)",
           "by_status": by, "things": rows}
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    tot = sum(v["segments"] for v in by.values())
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]["segments"]):
        print(f"{k:14s} things {v['things']:3d} segment-uses {v['segments']:4d} ({100 * v['segments'] / tot:.0f}%)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
