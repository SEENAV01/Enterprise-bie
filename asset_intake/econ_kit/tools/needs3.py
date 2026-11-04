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

STATUS.update({
    "stacked_bar": ("built_batch4", "segmentedBar(parts, cross, hide, glow)"),
    "price_tag": ("built_batch4", "priceTag(value, old, trend)"),
    "office_building": ("built_batch4", "building(kind=office)"), "government_building": ("built_batch4", "building(kind=government)"),
    "stock_exchange_building": ("built_batch4", "building(kind=exchange)"), "rural_bank_hut": ("built_batch4", "building(kind=hut)"),
    "house": ("built_batch4", "building(kind=house)"), "warehouse": ("built_batch4", "building(kind=warehouse)"),
    "dollar_note": ("built_batch4", "foreignNote(sign, value)"), "gauge": ("built_batch4", "gauge(value, text, label)"),
    "barrier_wall": ("built_batch4", "barrier(label)"), "hand": ("built_batch4", "hands(item, from, to)"),
    "piggy_bank": ("built_batch4", "piggyBank(label)"), "ruler": ("built_batch4", "ruler(min, max, value)"),
    "share_certificate": ("built_batch4", "paper(kind=share)"), "receipt_slip": ("built_batch4", "paper(kind=receipt)"),
    "server_rack": ("have_icon", "Font Awesome server / database"), "country_flag": ("replace", "country name card (no flags drawn by default)"),
    "india_map": ("decision", "Navin: Survey of India boundary; the official outline's licence is not clear yet (DataMeet conversion, 2018), so BIE shows a 'भारत' label"),
    "round_number_card": ("engine", "numbered step card"), "step_tracker": ("engine", "step counter"), "stage_with_spotlight": ("engine", "stage background"),
    "token_coin": ("have_v2", "coin"), "trading_desk": ("one_off", "person at screens"), "shoe": ("have_icon", "Fluent shoe"),
    "list_rail": ("engine", "list part"), "instrument_sidebar": ("engine", "road map sidebar"),
})
STATUS["committee_desk"] = ("built_batch3", "committee(n, name, sub, color)")
STATUS.update({   # batch 5 (4 Nov 2026): worlds, flow and the last recurring things
    "coin_jar": ("built_batch5", "coinJar(fill, label)"), "pillar": ("built_batch5", "pillars(labels, broken, glow, title)"),
    "briefcase": ("built_batch5", "briefcase(label, open)"), "budget_briefcase": ("built_batch5", "briefcase(label, open)"),
    "podium_steps": ("built_batch5", "podium(labels)"), "staircase": ("built_batch5", "staircase(labels, at, dir)"),
    "lender_desk": ("built_batch5", "desk(label, chair)"), "chair": ("built_batch5", "chair(kind, label)"), "armchair": ("built_batch5", "chair(kind=big)"),
    "rope": ("built_batch5", "rope(kind=rope|rod|chain, sag, angle, label)"), "court_building": ("built_batch5", "building(kind=court)"),
    "village_scene": ("built_batch5", "world(kind=village) or bg village"), "street_vendor": ("have_v2", "person + cart (batch 4)"),
    "factory": ("built_batch5", "world(kind=factory); a small factory icon = have_icon"),
    "coin": ("have_v2", "coin / coinStack"), "line_chart": ("engine", "graph part (curve_story)"),
    "shoe_rack": ("one_off", "one analogy video"), "title_sash": ("one_off", "one video"), "country_map": ("decision", "maps follow the official boundary decision"),
    "money_flow_diagram": ("built_batch5", "flow(nodes, edges, token, active)"), "circular_flow": ("built_batch5", "flow(layout=ring)"),
    "timeline": ("built_batch5", "timeline(events, zones, at, upto)"), "ownership_zone": ("built_batch5", "timeline(zones)"),
    "table_grid": ("built_batch5", "table(cols, rows, cells, glowRow, glowCol, upto)"), "graph_axes": ("built_batch5", "graph(lines, dots, drawIn)"),
    "line_chart": ("built_batch5", "graph(lines)"), "instrument_sidebar": ("built_batch5", "roadmap(items, at)"), "road_map_blob": ("built_batch5", "roadmap(items, at)"),
    "funnel": ("built_batch5", "funnel(label, top, bottom, flip)"), "cash_stack": ("have_v2", "noteBundle"), "cash_box": ("built_batch5", "coinJar / moneyBag"),
    "country_box": ("built_batch5", "world(kind=twoCountries) or a box node in flow"), "trading_desk": ("built_batch5", "world(kind=exchangeFloor)"),
    "budget_briefcase": ("built_batch5", "briefcase(label)"), "shield": ("have_icon", "Fluent shield"), "equals_sign": ("engine", "text"),
    "chocolate_bar": ("one_off", "a generic goods item"), "crown": ("have_icon", "Fluent crown (apex body)"), "truck": ("have_icon", "Fluent truck; flow token goods"),
    "percentage_badge": ("built_batch3", "disc(text)"), "rank_badge": ("built_batch5", "podium(labels)"), "scale_balance": ("have_icon", "Fluent balance scale"),
})
STATUS["india_map"] = ("decision", "Navin: Survey of India boundary; the official outline's licence is not clear yet (DataMeet conversion, 2018), so BIE shows a 'भारत' label")


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
           "how_counted": "a thing counts once per card segment it appears in; synonyms merged (aggregate3.ALIAS); built_batch3, built_batch4 and built_batch5 are all in BIE\u2019s engine",
           "by_status": by, "things": rows}
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    tot = sum(v["segments"] for v in by.values())
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]["segments"]):
        print(f"{k:14s} things {v['things']:3d} segment-uses {v['segments']:4d} ({100 * v['segments'] / tot:.0f}%)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
