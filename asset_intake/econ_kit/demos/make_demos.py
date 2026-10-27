"""Three template demos (structure copies of three reference teaching moments, in BIE's own look).

These are FIXTURES that exercise the economy kit, written by hand to test the templates; they are not lesson content.
In BIE the beats come from the script section and the plan from the director; this file only shows that the templates,
layout code and checks can carry those teaching moments.

  D1 demand_pull   — shop, a price that is struck and replaced, a crowd of buyers that grows and shrinks (ref E15)
  D2 phillips      — a curve that draws itself, a dot that walks along it, the natural rate and the long-run line (ref E02)
  D3 price_chain   — producer → wholesaler → retailer → consumer, prices at each step, PPI / WPI / CPI band (ref E20)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

D1 = {
    "id": "demand_pull", "theme": "paper", "grid": [12, 8],
    "beats": [
        {"beat_id": "b1", "say": "मान लीजिए एक दुकान पर चीनी के सिर्फ़ तीन पैकेट हैं, और दाम है पचास रुपये।"},
        {"beat_id": "b2", "say": "शुरू में दो ही खरीदार आते हैं, और दोनों पचास रुपये देने को तैयार हैं।"},
        {"beat_id": "b3", "say": "अब अचानक लोगों के पास पैसा बढ़ जाता है, और बारह खरीदार आ जाते हैं।"},
        {"beat_id": "b4", "say": "माल उतना ही है, लेकिन माँग बहुत ज़्यादा है।"},
        {"beat_id": "b5", "say": "तो दुकानदार दाम बढ़ाकर पैंसठ रुपये कर देता है।"},
        {"beat_id": "b6", "say": "अब वही खरीद पाते हैं जो पैंसठ दे सकते हैं, बाकी लौट जाते हैं।"},
        {"beat_id": "b7", "say": "माँग ने दाम को ऊपर खींच लिया, इसीलिए इसे डिमांड पुल इन्फ्लेशन कहते हैं।"},
    ],
    "nodes": [
        {"id": "tag", "kind": "text", "style": "tag", "text": "Demand-pull inflation", "cell": [0, 0, 5, 1], "cue": ["b1", "", 0.0]},
        {"id": "shop", "kind": "icon", "icon": "tw:1f3ea", "label": "SUPPLY · दुकान", "cell": [0, 2, 3, 3], "cue": ["b1", "दुकान"]},
        {"id": "goods", "kind": "crowd", "icon": "tw:1f4e6", "cell": [0, 5, 3, 1], "steps": [{"n": 3, "cue": ["b1", "पैकेट"]}]},
        {"id": "a1", "kind": "arrow", "from": "shop", "to": "price", "cue": ["b1", "दाम"]},
        {"id": "price", "kind": "value", "cell": [4, 3, 3, 1], "size": 64, "tone": "ink",
         "steps": [{"text": "₹50", "cue": ["b1", "पचास"]}, {"text": "₹65", "dir": "up", "cue": ["b5", "पैंसठ"]}]},
        {"id": "plabel", "kind": "text", "text": "PRICE", "style": "plain", "tone": "muted", "size": 26, "cell": [4, 2, 3, 1],
         "align": "left", "cue": ["b1", "दाम"]},
        {"id": "a2", "kind": "arrow", "from": "price", "to": "buyers", "cue": ["b2", "खरीदार"]},
        {"id": "buyers", "kind": "crowd", "icon": "tw:1f9cd", "cell": [8, 2, 4, 3], "cols": 4,
         "steps": [{"n": 2, "cue": ["b2", "खरीदार"]}, {"n": 12, "cue": ["b3", "बारह"]}, {"n": 3, "cue": ["b6", "बाकी"]}]},
        {"id": "dlabel", "kind": "text", "text": "DEMAND · खरीदार", "style": "plain", "tone": "muted", "size": 26,
         "cell": [8, 5, 4, 1], "align": "center", "cue": ["b2", "खरीदार"]},
        {"id": "money", "kind": "icon", "icon": "tw:1f4b0", "cell": [10, 0, 2, 2], "cue": ["b3", "पैसा"], "until_cue": ["b5", "", 0.0]},
        {"id": "dgts", "kind": "text", "style": "tag", "text": "Demand > Supply", "fill": "warm", "cell": [6, 0, 4, 1], "cue": ["b4", "माँग"]},
        {"id": "hg", "kind": "highlight", "target": "goods", "style": "dashed", "tone": "warm", "cue": ["b4", "माल"]},
        {"id": "hp", "kind": "highlight", "target": "price", "tone": "danger", "cue": ["b5", "दाम"]},
        {"id": "x1", "kind": "mark", "mark": "cross", "target": "dlabel", "pos": "tr", "cue": ["b6", "लौट"]},
        {"id": "sum", "kind": "callout", "style": "note", "cell": [3, 6, 6, 2], "size": 30,
         "text": "माँग ज़्यादा, माल उतना ही → माँग दाम को ऊपर खींचती है",
         "marks": [{"phrase": "दाम को ऊपर खींचती है", "cue": ["b7", "खींच"]}], "cue": ["b7", "माँग"]},
    ],
}


def phillips_points():
    pts = []
    for i in range(0, 37):
        u = 1.0 + i * 0.25
        pts.append([round(u, 3), round(0.6 + 8.6 / (u + 0.35), 3)])
    return pts


D2 = {
    "id": "phillips", "theme": "paper", "grid": [12, 8],
    "beats": [
        {"beat_id": "b1", "say": "Phillips curve बताती है कि महँगाई और बेरोज़गारी में उल्टा रिश्ता होता है।"},
        {"beat_id": "b2", "say": "जब बेरोज़गारी कम होती है, तब महँगाई ज़्यादा होती है।"},
        {"beat_id": "b3", "say": "और जब बेरोज़गारी बढ़ती है, तब महँगाई घट जाती है।"},
        {"beat_id": "b4", "say": "शॉर्ट टर्म में सरकार थोड़ी महँगाई सहकर बेरोज़गारी घटा सकती है।"},
        {"beat_id": "b5", "say": "लेकिन लॉन्ग टर्म में बेरोज़गारी अपनी नैचुरल दर पर लौट आती है, इसे NAIRU कहते हैं।"},
        {"beat_id": "b6", "say": "इसलिए लॉन्ग रन की Phillips curve एक सीधी खड़ी रेखा बन जाती है।"},
    ],
    "nodes": [
        {"id": "tag", "kind": "text", "style": "tag", "text": "Phillips curve", "cell": [0, 0, 3, 1], "cue": ["b1", "Phillips"]},
    ],
    "graph": {
        "plot": {"x": 0.1, "y": 0.2, "w": 0.52, "h": 0.6},
        "x_label": "बेरोज़गारी (Unemployment)", "y_label": "महँगाई (Inflation)", "x_domain": [0, 10.5], "y_domain": [0, 8],
        "axes_cue": ["b1", "Phillips"],
        "curves": [{"id": "sr", "points": phillips_points(), "tone": "accent", "label": "SRPC", "cue": ["b1", "उल्टा"],
                    "draw_frames": 36}],
        "dots": [{"id": "d", "curve": "sr", "tone": "danger", "drops": "xy",
                  "steps": [{"x": 1.6, "cue": ["b2", "कम"]}, {"x": 8.0, "cue": ["b3", "बढ़ती"]}, {"x": 3.0, "cue": ["b4", "घटा"]},
                            {"x": 4.6, "cue": ["b5", "लौट"]}]}],
        "shades": [{"id": "short", "x0": 1.2, "x1": 4.6, "tone": "accent", "hatch": True, "label": "Short run",
                    "cue": ["b4", "शॉर्ट"], "until_cue": ["b5", "लॉन्ग"]}],
        "guides": [{"id": "nairu", "x": 4.6, "tone": "warm", "dashed": True, "label": "NAIRU", "cue": ["b5", "नैचुरल"]},
                   {"id": "lrpc", "x": 4.6, "tone": "danger", "width": 8, "label": "", "cue": ["b6", "खड़ी"]}],
        "notes": [
            {"id": "n1", "fx": 0.68, "fy": 0.2, "fw": 0.27, "text": "बेरोज़गारी ↓  →  महँगाई ↑", "cue": ["b2", "महँगाई"]},
            {"id": "n2", "fx": 0.68, "fy": 0.33, "fw": 0.27, "text": "बेरोज़गारी ↑  →  महँगाई ↓", "cue": ["b3", "महँगाई"]},
            {"id": "n3", "fx": 0.68, "fy": 0.46, "fw": 0.27, "text": "Short run: थोड़ी महँगाई के बदले कम बेरोज़गारी",
             "tone": "accent", "cue": ["b4", "सरकार"]},
            {"id": "n4", "fx": 0.68, "fy": 0.62, "fw": 0.27, "text": "Long run: बेरोज़गारी NAIRU पर, रेखा खड़ी (LRPC)",
             "tone": "danger", "cue": ["b6", "रेखा"]},
        ],
    },
}

D3 = {
    "id": "price_chain", "theme": "paper", "grid": [12, 8],
    "beats": [
        {"beat_id": "b1", "say": "महँगाई नापने के लिए पहले देखते हैं कि एक चीज़ किन हाथों से गुज़रती है।"},
        {"beat_id": "b2", "say": "पहले फैक्ट्री उसे बनाती है, फिर थोक व्यापारी उसे खरीदता है।"},
        {"beat_id": "b3", "say": "थोक से वह दुकान तक जाती है, और दुकान से ग्राहक तक।"},
        {"beat_id": "b4", "say": "हर कदम पर दाम बढ़ता है, दस, फिर पंद्रह, फिर बीस रुपये।"},
        {"beat_id": "b5", "say": "फैक्ट्री वाले दाम से PPI बनता है, थोक दाम से WPI, और दुकान वाले दाम से CPI।"},
        {"beat_id": "b6", "say": "इस वीडियो में हमारा फोकस WPI है, यानी थोक दामों का index।"},
    ],
    "nodes": [
        {"id": "title", "kind": "text", "style": "title", "text": "महँगाई कैसे नापते हैं?", "cell": [0, 0, 12, 1], "size": 52,
         "cue": ["b1", "महँगाई"]},
        {"id": "f", "kind": "icon", "icon": "tw:1f3ed", "label": "PRODUCER", "cell": [0, 2, 2, 2], "cue": ["b2", "फैक्ट्री"]},
        {"id": "w", "kind": "icon", "icon": "fa:solid/warehouse", "label": "WHOLESALER", "cell": [3, 2, 2, 2], "cue": ["b2", "थोक"]},
        {"id": "r", "kind": "icon", "icon": "tw:1f3ea", "label": "RETAILER", "cell": [6, 2, 2, 2], "cue": ["b3", "दुकान"]},
        {"id": "c", "kind": "icon", "icon": "tw:1f9cd", "label": "CONSUMER", "cell": [9, 2, 2, 2], "cue": ["b3", "ग्राहक"]},
        {"id": "a1", "kind": "arrow", "from": "f", "to": "w", "from_side": "r", "to_side": "l", "cue": ["b2", "खरीदता"]},
        {"id": "a2", "kind": "arrow", "from": "w", "to": "r", "from_side": "r", "to_side": "l", "cue": ["b3", "दुकान"]},
        {"id": "a3", "kind": "arrow", "from": "r", "to": "c", "from_side": "r", "to_side": "l", "cue": ["b3", "ग्राहक"]},
        {"id": "v1", "kind": "value", "align": "center", "cell": [0, 4, 2, 1], "size": 48, "steps": [{"text": "₹10", "cue": ["b4", "दस"]}]},
        {"id": "v2", "kind": "value", "align": "center", "cell": [3, 4, 2, 1], "size": 48, "steps": [{"text": "₹15", "dir": "up", "cue": ["b4", "पंद्रह"]}]},
        {"id": "v3", "kind": "value", "align": "center", "cell": [6, 4, 2, 1], "size": 48, "steps": [{"text": "₹20", "dir": "up", "cue": ["b4", "बीस"]}]},
        {"id": "ppi", "kind": "text", "style": "box", "text": "PPI · Producer Price Index", "size": 26, "cell": [0, 6, 3, 1], "cue": ["b5", "PPI"]},
        {"id": "wpi", "kind": "text", "style": "box", "text": "WPI · Wholesale Price Index", "size": 26, "cell": [3, 6, 3, 1], "cue": ["b5", "WPI"]},
        {"id": "cpi", "kind": "text", "style": "box", "text": "CPI · Consumer Price Index", "size": 26, "cell": [6, 6, 3, 1], "cue": ["b5", "CPI"]},
        {"id": "hw", "kind": "highlight", "target": "wpi", "tone": "warm", "cue": ["b6", "फोकस"]},
        {"id": "tk", "kind": "mark", "mark": "tick", "target": "wpi", "pos": "tr", "cue": ["b6", "WPI"]},
    ],
    "focus": [{"cue": ["b6", "फोकस"], "ids": ["w", "wpi", "hw", "tk", "v2", "title", "a1", "a2"]}],
}

D4 = {
    "id": "real_gdp", "theme": "paper", "grid": [12, 8],
    "beats": [
        {"beat_id": "b1", "say": "GDP दो तरह से नापी जाती है, नॉमिनल और रियल।"},
        {"beat_id": "b2", "say": "मान लीजिए देश हर साल सिर्फ़ एक लैपटॉप बनाता है।"},
        {"beat_id": "b3", "say": "पहले साल उसका दाम दस हज़ार है, तो GDP भी दस हज़ार।"},
        {"beat_id": "b4", "say": "अगले साल दस प्रतिशत महँगाई से दाम ग्यारह हज़ार, फिर बारह हज़ार एक सौ हो जाता है।"},
        {"beat_id": "b5", "say": "उत्पादन वही एक लैपटॉप है, फिर भी नॉमिनल GDP बढ़ती दिख रही है।"},
        {"beat_id": "b6", "say": "इसलिए महँगाई हटाकर, बेस ईयर के दाम पर जो GDP निकलती है, उसे रियल GDP कहते हैं।"},
    ],
    "nodes": [
        {"id": "tr", "kind": "tree", "root": "GDP", "children": [{"text": "Nominal GDP", "cue": ["b1", "नॉमिनल"]},
                                                                 {"text": "Real GDP", "cue": ["b1", "रियल"]}],
         "cell": [0, 0, 5, 3], "cue": ["b1", "GDP"], "size": 30},
        {"id": "lap", "kind": "icon", "icon": "tw:1f4bb", "label": "1 laptop / year", "cell": [7, 0, 3, 2], "cue": ["b2", "लैपटॉप"]},
        {"id": "tab", "kind": "table", "cell": [0, 3, 8, 3], "columns": ["Year", "Quantity", "Price", "Nominal GDP"],
         "rows": [{"cells": ["Year 1", "1", "₹10,000", "₹10,000"], "cue": ["b3", "पहले"]},
                  {"cells": ["Year 2", "1", "₹11,000", "₹11,000"], "cue": ["b4", "ग्यारह"]},
                  {"cells": ["Year 3", "1", "₹12,100", "₹12,100"], "cue": ["b4", "बारह"]}],
         "highlights": [{"col": 1, "cue": ["b5", "उत्पादन"], "until_cue": ["b5", "नॉमिनल"], "tone": "band"},
                        {"col": 3, "cue": ["b5", "नॉमिनल"], "tone": "note"}]},
        {"id": "infl", "kind": "text", "style": "tag", "text": "Inflation 10%", "fill": "danger", "cell": [9, 3, 3, 1], "cue": ["b4", "महँगाई"]},
        {"id": "x", "kind": "mark", "mark": "cross", "target": "tr_0", "pos": "tr", "cue": ["b5", "बढ़ती"]},
        {"id": "real", "kind": "callout", "style": "note", "cell": [8, 4, 4, 2], "size": 28,
         "text": "Real GDP = base year के दाम पर उत्पादन (महँगाई हटाकर)",
         "marks": [{"phrase": "महँगाई हटाकर", "cue": ["b6", "हटाकर"]}], "cue": ["b6", "बेस"]},
        {"id": "tk", "kind": "mark", "mark": "tick", "target": "tr_1", "pos": "tr", "cue": ["b6", "रियल"]},
    ],
}

# D1 with "L3 touches": the same plan, plus depth, life, flowing goods and money, and a camera that follows the story.
import copy as _copy
D1B = _copy.deepcopy(D1)
D1B["id"] = "demand_pull_touches"
D1B["touches"] = True
for _n in D1B["nodes"]:
    if _n["id"] == "a1":
        _n["flow"] = {"icon": "tw:1f4e6", "count": 3, "period": 45, "size": 34}
    if _n["id"] == "a2":
        _n["flow"] = {"icon": "tw:1fa99", "count": 4, "period": 36, "size": 30, "reverse": True, "cue": ["b2", "तैयार"]}

# D1 as a full L3 world: the same beats, told inside a street with a shop, BIE's own walking people and a camera that
# moves through parallax layers (block world_scene, compiled by tools/world_plan.py).
D1C = {
    "id": "demand_pull_world", "world_width": 5200, "beats": _copy.deepcopy(D1["beats"]),
    "elements": [
        {"id": "fg1", "kind": "foreground", "x": 1750}, {"id": "fg2", "kind": "foreground", "x": 3900},
        {"id": "lamp1", "kind": "lamp", "x": 2050}, {"id": "lamp2", "kind": "lamp", "x": 3250},
        {"id": "shop", "kind": "shop", "x": 2600, "sign": "किराना स्टोर", "packets": [{"n": 3, "cue": ["b1", "पैकेट"]}, {"n": 0, "cue": ["b6", "खरीद"]}]},
        {"id": "tag", "kind": "price_tag", "x": 2870, "y": 560, "string": 60,
         "steps": [{"text": "₹50", "cue": ["b1", "पचास"]}, {"text": "₹65", "dir": "up", "cue": ["b5", "पैंसठ"]}],
         "lift": {"cue": ["b7", "खींच"], "dy": 130}},
        {"id": "sup", "kind": "label", "x": 2030, "y": 470, "text": "SUPPLY · 3 पैकेट", "fill": "rgba(46,134,222,0.9)", "cue": ["b1", "पैकेट"],
         "until_cue": ["b2", "", 0.0]},
        {"id": "crowd", "kind": "crowd", "x0": 2330, "spacing": 120, "enter_x": 3950, "exit_x": 4300, "face": -1, "seed": 4,
         "steps": [{"n": 2, "cue": ["b2", "खरीदार"]}, {"n": 12, "cue": ["b3", "बारह"]}, {"n": 3, "cue": ["b6", "बाकी"]}],
         "carry": {"cue": ["b6", "खरीद"], "n": 3}},
        {"id": "d2", "kind": "label", "x": 3250, "y": 560, "text": "DEMAND · 2", "fill": "rgba(230,126,34,0.92)", "cue": ["b2", "खरीदार"],
         "until_cue": ["b3", "बारह"]},
        {"id": "rain", "kind": "coin_rain", "x0": 2250, "x1": 3600, "count": 46, "cue": ["b3", "पैसा"], "until_cue": ["b3", "बारह"]},
        {"id": "d12", "kind": "label", "x": 3330, "y": 700, "text": "DEMAND · 12", "fill": "rgba(230,126,34,0.92)", "cue": ["b3", "बारह"],
         "until_cue": ["b6", "बाकी"]},
        {"id": "bal", "kind": "balance", "x": 3600, "y": 230, "tilt": 16, "cue": ["b4", "माल"], "tilt_cue": ["b4", "ज़्यादा"],
         "until_cue": ["b5", "", 0.0]},
        {"id": "d3", "kind": "label", "x": 3560, "y": 620, "text": "₹65 देने वाले: 3", "fill": "rgba(39,174,96,0.92)", "cue": ["b6", "बाकी"]},
        {"id": "pull", "kind": "pull_arrow", "x": 3090, "y0": 840, "y1": 480, "text": "DEMAND", "cue": ["b7", "खींच"]},
        {"id": "title", "kind": "title", "text": "DEMAND-PULL INFLATION", "cue": ["b7", "डिमांड"]},
    ],
    "camera": [
        {"cue": ["b1", "", 0.0], "x": 1500, "y": 560, "zoom": 0.9, "frames": 1},
        {"cue": ["b1", "दुकान"], "x": 2600, "y": 560, "zoom": 1.15, "frames": 60},
        {"cue": ["b1", "पचास"], "x": 2760, "y": 520, "zoom": 1.6, "frames": 40},
        {"cue": ["b2", "शुरू"], "x": 2700, "y": 600, "zoom": 1.1, "frames": 40},
        {"cue": ["b3", "पैसा"], "x": 2800, "y": 540, "zoom": 0.95, "frames": 40},
        {"cue": ["b3", "बारह"], "x": 2950, "y": 600, "zoom": 0.85, "frames": 50},
        {"cue": ["b4", "माल"], "x": 3050, "y": 470, "zoom": 0.85, "frames": 40},
        {"cue": ["b5", "दाम"], "x": 2870, "y": 540, "zoom": 1.7, "frames": 40},
        {"cue": ["b6", "वही"], "x": 2950, "y": 600, "zoom": 0.9, "frames": 45},
        {"cue": ["b7", "माँग"], "x": 2850, "y": 520, "zoom": 1.0, "frames": 45},
    ],
}

if __name__ == "__main__":
    json.dump(D1C, open(os.path.join(HERE, D1C["id"] + ".world.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for d in (D1, D2, D3, D4, D1B):
        json.dump(d, open(os.path.join(HERE, d["id"] + ".plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", [d["id"] for d in (D1, D2, D3, D4, D1B)])
