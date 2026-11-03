"""v2 demo scene plan -> spec.json (Claude's demo, not BIE output).
For every line: what is seen (the thing said) and what happens (the action said), on the word it is said."""
import json, math, sys
from timeline import Timeline

T = Timeline()
C = T.cue
FLOOR = 885
POSES = {"stand": (8, 5, 8, 5), "give": (80, 0, 10, 5), "receive": (62, 18, 10, 5), "hold": (20, 85, 10, 5), "holdBoth": (22, 80, 22, 80),
         "think": (28, 145, 10, 5), "point": (120, 5, 10, 5), "shrug": (40, 110, 40, 110), "wave": (150, 25, 10, 5), "carry": (160, 40, 10, 5),
         "write": (35, 75, 10, 5), "walk": (10, 5, 10, 5), "refuse": (55, 105, 10, 5)}


def hand(H, s, pose):
    a1, a2 = POSES.get(pose, POSES["stand"])[:2]
    r = math.radians
    sx, sy = 0.12 * H * s, -0.76 * H
    ex, ey = sx + math.sin(r(a1)) * 0.17 * H * s, sy + math.cos(r(a1)) * 0.17 * H
    return ex + math.sin(r(a1 + a2)) * 0.16 * H * s, ey + math.cos(r(a1 + a2)) * 0.16 * H


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def x_at(el, t):
    st = {"x": el.get("x", 0), "y": el.get("y", 0)}
    for k in el.get("keys", []):
        if t <= k["t"]:
            break
        p = ease((t - k["t"]) / k.get("d", 0.6))
        for f in ("x", "y"):
            if k.get(f) is not None:
                st[f] += (k[f] - st[f]) * p
    return st["x"], st["y"]


def facing_at(el, t):
    s = el.get("facing", 1)
    for f in el.get("facings", []):
        if t >= f["t"]:
            s = f["s"]
    return s


SHOTS = []


class Shot:
    def __init__(self, sid, lines, bg="paper", kicker=None, fg=None):
        self.id, self.lines, self.bg, self.kicker, self.fg = sid, lines, bg, kicker, fg
        self.t0 = T.L(lines[0])["t0"] - 0.35
        self.els, self.cam = [], []
        SHOTS.append(self)

    def add(self, el):
        el.setdefault("t0", self.t0)
        self.els.append(el)
        return el

    # ---- element helpers
    def person(self, pid, look, x, t0=None, y=FLOOR, h=440, facing=1, pose="stand", expr="smile", z=10, t1=None):
        return self.add({"id": pid, "kind": "person", "look": look, "x": x, "y": y, "h": h, "facing": facing, "pose": pose, "expr": expr,
                         "t0": self.t0 if t0 is None else t0, "t1": t1, "z": z, "poses": [], "exprs": [], "holds": [], "facings": [],
                         "walks": [], "shakes": [], "nods": [], "keys": []})

    def item(self, spec, x, y, t0=None, t1=None, s=1, z=20, keys=None, enter="pop", **kw):
        el = dict(spec, x=x, y=y, s=s, z=z, t0=self.t0 if t0 is None else t0, t1=t1, enter=enter, keys=keys or [])
        el.update(kw)
        return self.add(el)

    def text(self, text, x, y, t0=None, t1=None, size=46, style="tag", w=None, z=40, **kw):
        el = {"text": text, "size": size, "style": style, "x": x, "y": y, "t0": self.t0 if t0 is None else t0, "t1": t1, "z": z}
        if w:
            el["w"] = w
        el.update(kw)
        return self.add(el)

    def mark(self, kind, x, y, t0, t1=None, w=120, z=45, **kw):
        return self.add(dict({"kind": "mark", "mark": kind, "x": x, "y": y, "w": w, "t0": t0, "t1": t1, "z": z, "enter": "none"}, **kw))

    def arrow(self, x1, y1, x2, y2, t0, t1=None, z=30, **kw):
        return self.add(dict({"kind": "arrow", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "x": 0, "y": 0, "t0": t0, "t1": t1, "z": z, "enter": "none"}, **kw))

    def bubble(self, of, content, t0, t1=None, w=260, kind="think", dx=200, dy=-560, z=48, **kw):
        return self.add(dict({"kind": "bubble", "of": of["id"] if isinstance(of, dict) else None, "content": content, "w": w, "kind2": kind,
                              "t0": t0, "t1": t1, "dx": dx, "dy": dy, "z": z, "tail": -1 if dx > 0 else 1, "x": 0, "y": 0}, **kw))

    def rect(self, x, y, w, h, t0=None, t1=None, z=1, **kw):
        return self.add(dict({"kind": "rect", "x": x, "y": y, "w": w, "h": h, "t0": self.t0 if t0 is None else t0, "t1": t1, "z": z, "enter": "fade"}, **kw))

    def camera(self, t, x=960, y=540, z=1.0, d=1.0):
        self.cam.append({"t": t, "d": d, "x": x, "y": y, "z": z})

    # ---- actions
    def pose(self, p, t, pose):
        p["poses"].append({"t": t, "pose": pose})

    def expr(self, p, t, e):
        p["exprs"].append({"t": t, "expr": e})

    def hold(self, p, t, spec):
        p["holds"].append({"t": t, "item": spec})

    def walk(self, p, t, to_x, d=1.4):
        x, _ = x_at(p, t)
        p["facings"].append({"t": t, "s": 1 if to_x > x else -1})
        p["keys"].append({"t": t, "d": d, "x": to_x})
        p["walks"].append({"t": t, "d": d})
        self.pose(p, t, "walk")

    def face(self, p, t, s):
        p["facings"].append({"t": t, "s": s})

    def give(self, spec, a, b, t, d=0.9, keep=True, z=70, drop_to=None):
        """A hands the thing to B: A's arm goes out, the thing travels hand to hand, B takes it."""
        self.pose(a, t - 0.4, "give")
        sa = facing_at(a, t)
        ax, ay = x_at(a, t)
        hx, hy = hand(a["h"], sa, "give")
        bx, by = x_at(b, t + d)
        sb = facing_at(b, t + d)
        rx, ry = hand(b["h"], sb, "receive")
        a["holds"].append({"t": t, "item": None})
        end = (bx + rx, by + ry) if drop_to is None else drop_to
        mv = self.item({"group": [spec]}, ax + hx, ay + hy, t0=t, t1=t + d + (0.05 if keep or drop_to is None else 99), z=z, enter="none",
                       keys=[{"t": t, "d": d, "x": end[0], "y": end[1]}])
        self.pose(a, t + 0.55, "stand")
        if drop_to is None:
            self.pose(b, t + 0.15, "receive")
            if keep:
                self.pose(b, t + d, "hold")
                hb = hand(b["h"], sb, "hold")
                b["holds"].append({"t": t + d, "item": spec})
            else:
                self.pose(b, t + d + 0.2, "stand")
        else:
            mv["t1"] = None
        return mv


# ----------------------------------------------------------------- things (item specs)
def SACK(label="", content="wheat", w=220):
    return {"draw": "sack", "p": {"w": w, "label": label, "content": content}, "y": w * 0.5}


def HSACK(label="", content="wheat", w=110):
    return {"draw": "sack", "p": {"w": w, "label": label, "content": content}, "y": w * 0.55}


CLOTH = lambda w=170: {"draw": "clothRoll", "p": {"w": w}, "y": w * 0.25}
SALTP = lambda w=90: {"draw": "saltPacket", "p": {"w": w}, "y": w * 0.7}
NOTE = lambda v=500, w=170: {"draw": "note", "p": {"value": v, "w": w}}
COIN = lambda metal="gold", r=40: {"draw": "coin", "p": {"metal": metal, "r": r}}
OIL = lambda w=110: {"draw": "oilTin", "p": {"w": w}, "y": w * 0.6}
A = lambda name, w=160: {"asset": name, "w": w}
D_ = lambda fn, w=None, **p: {"draw": fn, "p": dict(p, **({"w": w} if w else {}))}


def mini(look, s=1, x=0, y=0, pose="stand", facing=1, h=200):
    return {"draw": "__person__", "look": look, "h": h, "pose": pose, "facing": facing, "x": x, "y": y, "s": s}


# ================================================================= SHOTS
# ---- 1 (l01) a farmer with only wheat
s = Shot("A", ["l01"], "village")
ramu = s.person("ramu", "ramu", 760, facing=1)
s.item(SACK("गेहूँ", w=240), 1010, FLOOR, t0=C("l01", "गेहूँ"))
s.item({"group": [dict(NOTE(500, 200), x=-40, y=-10), dict(COIN("gold", 44), x=90, y=30)]}, 1330, 360, t0=C("l01", "पैसा"), t1=C("l01", "सिर्फ़") + 1.2)
s.mark("cross", 1350, 370, C("l01", "नहीं"), t1=C("l01", "सिर्फ़") + 1.2, w=230)
s.bubble(ramu, CLOTH(240), C("l01", "कपड़ा"), w=330, dx=250, dy=-600)
s.mark("question", 1250, 210, C("l01", "क्या"), w=130)
s.pose(ramu, C("l01", "कपड़ा"), "think")
s.camera(0, 960, 560, 1.08, 0.1)

# ---- 2 (l02-l05) barter in the village market
s = Shot("B", ["l02", "l03", "l04", "l05"], "haat")
ramu = s.person("ramu", "ramu", 640, facing=1)
mohan = s.person("mohan", "mohan", 1300, facing=-1, t0=C("l02", "मोहन"))
big = s.item(SACK("10 kg", w=230), 400, FLOOR, steps=None)
s.text("रामू · किसान", 640, 360, t0=C("l02", "रामू"), t1=C("l02", "मोहन") + 1.5, size=40)
s.text("मोहन · कपड़े वाला", 1300, 360, t0=C("l02", "मोहन"), t1=C("l03", "", 0) if False else C("l03", frac=0.05), size=40)
s.item(D_("clothStack", 230), 1560, FLOOR, t0=C("l02", "कपड़ा"))
kg = s.text("10 kg", 400, 640, t0=C("l02", "दस किलो"), size=50, style="pill", bg="#f29f05", z=42, steps=[{"t": C("l04", "आठ किलो"), "text": "8 kg"}])
t_two = C("l03", "दो किलो")
s.pose(ramu, t_two - 0.3, "hold")
s.hold(ramu, t_two, HSACK("2 kg", w=110))
s.give(HSACK("2 kg", w=110), ramu, mohan, C("l03", "देता"), d=0.9, keep=False, drop_to=(1170, FLOOR))
t_cl = C("l03", "एक मीटर")
s.pose(mohan, t_cl - 0.6, "hold")
s.hold(mohan, t_cl - 0.5, CLOTH(150))
s.give(CLOTH(150), mohan, ramu, t_cl + 0.2, d=0.9)
s.text("1 metre", 840, 470, t0=C("l04", "एक मीटर"), size=46, style="pill", bg="#e0533d", z=42)
s.expr(ramu, C("l04", "आ गया"), "happy"); s.expr(mohan, C("l04", "आ गया"), "happy")
t5 = C("l05", "चीज़")
s.arrow(760, 300, 1180, 300, t5, width=12, bend=-0.18, color="#2fb463")
s.arrow(1180, 330, 760, 330, t5 + 0.4, width=12, bend=-0.18, color="#e0533d")
s.item(D_("wheat", 70), 970, 205, t0=t5 + 0.2, keys=[])
s.item(CLOTH(90), 970, 430, t0=t5 + 0.5)
s.text("Barter system", 960, 140, t0=C("l05", "barter"), size=84, style="title", z=50)
s.camera(C("l05", frac=0.0), 960, 520, 1.0)

# ---- 3 (l06-l08) goods or services, no money in the middle
s = Shot("C", ["l06", "l07", "l08"], "paper", kicker="Barter क्या है")
t_end_panels = C("l08", frac=0.0) + 0.2
s.rect(500, 440, 820, 600, t0=C("l06", "सामान"), t1=t_end_panels, z=1, fill="#ffffff")
s.text("सामान ⇄ सामान", 500, 205, t0=C("l06", "सामान"), t1=t_end_panels, size=56, style="plain")
s.item(SACK("गेहूँ", w=200), 330, 600, t0=C("l06", "सामान"), t1=t_end_panels)
s.item(D_("clothRoll", 220), 680, 560, t0=C("l06", "सामान") + 0.2, t1=t_end_panels)
s.arrow(410, 380, 600, 380, C("l06", "सीधे"), t1=t_end_panels, width=10, bend=-0.25, color="#2fb463")
s.arrow(600, 640, 410, 640, C("l06", "सीधे") + 0.3, t1=t_end_panels, width=10, bend=-0.25, color="#e0533d")
s.rect(1420, 440, 820, 600, t0=C("l06", "सेवा", nth=2), t1=t_end_panels, z=1, fill="#ffffff")
s.text("सेवा (काम) ⇄ सामान", 1420, 205, t0=C("l06", "सेवा", nth=2), t1=t_end_panels, size=56, style="plain")
mo = s.person("mohan3", "mohan", 1250, y=700, h=330, facing=1, t0=C("l06", "सेवा", nth=2), t1=t_end_panels, z=12)
s.hold(mo, C("l06", "सेवा", nth=2), A("wrench", 110))
s.pose(mo, C("l06", "सेवा", nth=2), "hold")
bike = s.item(A("bicycle", 240), 1560, 610, t0=C("l06", "सेवा", nth=2), t1=t_end_panels,
              keys=[{"t": C("l07", "ठीक"), "d": 0.15, "r": -4}, {"t": C("l07", "ठीक") + 0.15, "d": 0.15, "r": 4}, {"t": C("l07", "ठीक") + 0.3, "d": 0.15, "r": -3}, {"t": C("l07", "ठीक") + 0.45, "d": 0.2, "r": 0}])
s.mark("tick", 1650, 470, C("l07", "ठीक") + 0.6, t1=t_end_panels, w=90)
s.item(HSACK("2 kg", w=120), 1600, 760, t0=C("l07", "बदले"), t1=t_end_panels, keys=[{"t": C("l07", "दो किलो"), "d": 0.8, "x": 1330, "y": 760}])
s.camera(C("l07", frac=0.0), 1420, 480, 1.45, 0.8)
s.camera(C("l08", frac=0.0) - 0.3, 960, 540, 1.0, 0.6)
t8 = C("l08", "बीच")
for row, (yy, label) in enumerate([(330, "Barter"), (690, "आज")]):
    tt = t8 if row == 0 else C("l08", "आज")
    s.text(label, 240, yy, t0=tt, size=50, style="pill", bg="#2b2b33" if row == 0 else "#3a7bd5")
    s.item({"draw": "__person__", "look": "ramu", "h": 230, "pose": "stand", "facing": 1}, 520, yy + 115, t0=tt)
    s.arrow(620, yy - 20, 840, yy - 20, tt + 0.2, width=9)
    s.arrow(1080, yy - 20, 1300, yy - 20, tt + 0.4, width=9)
    s.item({"draw": "__person__", "look": "mohan", "h": 230, "pose": "stand", "facing": -1}, 1420, yy + 115, t0=tt)
s.rect(960, 310, 220, 170, t0=t8, z=5, fill="#ffffff", stroke="#9a9aa6", sw=6, alpha=0.9)
s.mark("question", 960, 305, t8 + 0.3, w=110, color="#9a9aa6")
s.rect(960, 670, 220, 170, t0=C("l08", "आज"), z=5, fill="#ffffff", stroke="#3a7bd5", sw=6)
s.item(NOTE(100, 180), 960, 670, t0=C("l08", "रुपया"))
s.text("Medium of exchange = बीच का ज़रिया", 960, 895, t0=C("l08", "medium"), size=48, style="pill", bg="#3a7bd5", fill="#ffffff")

# ---- 4 (l09-l12) four features as cards, camera visits each
s = Shot("D", ["l09", "l10", "l11", "l12"], "paper", kicker="Barter की 4 पहचान")
CARDS = [(500, 300), (1420, 300), (500, 700), (1420, 700)]
feat = [("l09", "पैसे का इस्तेमाल नहीं", "No use of money"), ("l10", "सामान-सेवा का सीधा लेन-देन", "Direct exchange"),
        ("l11", "भाव दोनों मिलकर तय करें", "Mutual agreement"), ("l12", "पहले आम, आज कम", "Early civilizations, आज छोटे लेन-देन")]
for i, ((cx, cy), (lid, hi, en)) in enumerate(zip(CARDS, feat)):
    t0 = T.L(lid)["t0"]
    s.rect(cx, cy, 860, 360, t0=t0, z=1)
    s.text(str(i + 1), cx - 385, cy - 135, t0=t0, size=40, style="pill", bg="#f29f05", z=3)
    s.text(hi, cx + 175, cy - 40, t0=t0 + 0.3, size=48, style="plain", w=460, z=3)
    s.text(en, cx + 175, cy + 80, t0=t0 + 0.6, size=38, style="plain", fill="#7b61ff", w=460, z=3)
    s.camera(t0 - 0.2, cx, cy, 1.55, 0.7)
# card visuals
cx, cy = CARDS[0]; t0 = T.L("l09")["t0"]
s.item(NOTE(500, 230), cx - 220, cy + 10, t0=t0 + 0.2, z=4); s.mark("cross", cx - 220, cy + 10, C("l09", "नहीं"), w=200, z=5)
cx, cy = CARDS[1]; t0 = T.L("l10")["t0"]
s.item(D_("wheat", 120), cx - 330, cy + 60, t0=t0 + 0.2, z=4); s.item(CLOTH(130), cx - 120, cy + 60, t0=t0 + 0.3, z=4)
s.arrow(cx - 300, cy - 40, cx - 140, cy - 40, C("l10", "सीधा"), width=8, bend=-0.3, color="#2fb463", z=4)
s.arrow(cx - 140, cy + 110, cx - 300, cy + 110, C("l10", "सीधा") + 0.3, width=8, bend=-0.3, color="#e0533d", z=4)
cx, cy = CARDS[2]; t0 = T.L("l11")["t0"]
s.item({"draw": "__person__", "look": "ramu", "h": 230, "pose": "give", "facing": 1}, cx - 330, cy + 150, t0=t0 + 0.2, z=4)
s.item({"draw": "__person__", "look": "mohan", "h": 230, "pose": "give", "facing": -1}, cx - 130, cy + 150, t0=t0 + 0.3, z=4)
s.item(A("handshake", 90), cx - 230, cy - 20, t0=C("l11", "दोनों"), z=5)
s.text("2 kg = 1 m", cx - 230, cy - 120, t0=C("l11", "तय"), size=40, style="pill", bg="#2fb463", z=6)
s.add({"kind": "person", "look": "ramu", "h": 0, "x": -999, "y": -999, "t0": 0, "t1": 0, "poses": [], "exprs": [], "holds": [], "facings": [], "walks": [], "shakes": [], "nods": [], "keys": []})
cx, cy = CARDS[3]; t0 = T.L("l12")["t0"]
s.item(A("hut", 120), cx - 340, cy + 20, t0=C("l12", "पुराने"), z=4)
s.text("पहले", cx - 340, cy + 115, t0=C("l12", "पुराने"), size=32, style="plain", z=4)
s.item({"draw": "__person__", "look": "sita", "h": 190, "pose": "give", "facing": 1}, cx - 225, cy + 150, t0=C("l12", "पड़ोसियों"), z=4)
s.item({"draw": "__person__", "look": "villager", "h": 190, "pose": "give", "facing": -1}, cx - 75, cy + 150, t0=C("l12", "पड़ोसियों") + 0.2, z=4)
s.item(D_("bowl", 60), cx - 150, cy + 10, t0=C("l12", "छोटे"), z=5)
s.item(D_("veg", 60), cx - 150, cy - 50, t0=C("l12", "छोटे") + 0.2, z=5)
s.text("आज", cx - 150, cy - 130, t0=C("l12", "आज"), size=32, style="pill", bg="#3a7bd5", fill="#fff", z=6)
s.camera(C("l12", frac=0.85), 960, 520, 1.0, 0.9)

# ---- 5 (l13-l16) double coincidence of wants
s = Shot("E", ["l13", "l14", "l15", "l16"], "haat", kicker="मुश्किल 1: Double coincidence of wants")
s.text("Double coincidence of wants", 960, 170, t0=C("l13", "double"), t1=T.L("l14")["t0"] + 0.2, size=76, style="title", z=50)
s.text("दोनों की ज़रूरत, एक साथ", 960, 275, t0=C("l13", "double") + 0.6, size=46, style="plain", z=50, t1=C("l14", frac=0.0) + 0.5)
ramu = s.person("ramu", "ramu", 520, facing=1, t0=C("l14", frac=0.0) - 0.2, z=15)
s.pose(ramu, C("l14", frac=0.0), "hold"); s.hold(ramu, C("l14", frac=0.0), HSACK("गेहूँ", w=110))
mohan = s.person("mohan", "mohan", 1000, facing=-1, t0=C("l14", frac=0.0) - 0.1, t1=C("l15", frac=0.0) + 0.3)
s.item(D_("clothStack", 160), 1170, FLOOR, t0=C("l14", frac=0.0), t1=C("l15", frac=0.0) + 0.3)
s.bubble(mohan, OIL(150), C("l14", "तेल"), t1=C("l15", frac=0.0) + 0.3, w=260, dx=-180, dy=-590)
s.pose(ramu, C("l14", "तो"), "give")
s.add({"kind": "mark", "mark": "cross", "x": 520 + hand(440, 1, "give")[0], "y": FLOOR + hand(440, 1, "give")[1] - 30, "w": 150, "t0": C("l14", "किस"), "t1": C("l15", frac=0.0) + 0.3, "z": 60, "enter": "none"})
mohan["shakes"].append({"t": C("l14", "किस"), "d": 1.1}); s.expr(mohan, C("l14", "तेल"), "frown")
s.pose(ramu, C("l15", frac=0.0), "hold")
kam = s.person("kamla", "kamla", 1250, facing=-1, t0=C("l15", frac=0.0) + 0.3)
s.item(D_("clothStack", 150), 1400, FLOOR, t0=C("l15", frac=0.0) + 0.3)
raju = s.person("raju", "raju", 1720, facing=-1, t0=C("l15", frac=0.0) + 0.4)
s.item(D_("clothStack", 150), 1880, FLOOR, t0=C("l15", frac=0.0) + 0.4)
s.camera(C("l15", frac=0.0), 1250, 540, 1.0, 1.2)
s.walk(ramu, C("l15", frac=0.05), 1010, 1.6)
s.bubble(kam, SALTP(110), C("l15", "कपड़ा"), t1=C("l15", "गेहूँ") + 1.2, w=220, dx=-170, dy=-580)
s.mark("cross", 1080, 330, C("l15", "जिसे"), t1=C("l15", "गेहूँ") + 1.2, w=150)
s.walk(ramu, C("l15", "गेहूँ") - 0.6, 1480, 1.5)
s.bubble(raju, D_("wheat", 130), C("l16", frac=0.0), w=230, dx=-170, dy=-580)
s.bubble(ramu, CLOTH(160), C("l16", frac=0.0) + 0.3, w=230, dx=170, dy=-580)
s.mark("tick", 1600, 260, C("l16", "मिल"), w=140)
s.expr(ramu, C("l16", "मिल"), "happy"); s.expr(raju, C("l16", "मिल"), "happy")
s.text("ऐसा साथी ढूँढना मुश्किल", 1250, 470, t0=C("l16", "ढूँढना"), size=46, style="pill", bg="#e5484d", fill="#fff", z=55)
s.item(A("magnifying_glass_tilted_left", 110), 1020, 470, t0=C("l16", "ढूँढना") + 0.2, z=56)

# ---- 6 (l17) no common measure of value: a web of rates
s = Shot("F", ["l17"], "paper", kicker="मुश्किल 2: No common measure of value")
P5 = [(960, 250, SACK("गेहूँ", w=170), "गेहूँ"), (1460, 470, CLOTH(190), "कपड़ा"), (1260, 820, D_("matka", 130), "मटका"),
      (660, 820, OIL(120), "तेल"), (460, 470, SALTP(110), "नमक")]
for i, (x, y, spec, name) in enumerate(P5):
    s.item(spec, x, y + 60, t0=C("l17", frac=0.02 + i * 0.03), z=20, s=1.45)
for k, (i, j) in enumerate([(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]):
    (x1, y1, *_), (x2, y2, *_) = P5[i], P5[j]
    t0 = C("l17", "एक मीटर") if (i, j) == (0, 1) else C("l17", "मटका") if (i, j) == (0, 2) else C("l17", "हर जोड़ी") + k * 0.12
    s.arrow(x1, y1, x2, y2, t0, width=5, color="#9a9aa6", z=5, dashed=True)
    lab = "1 m = 2 kg" if (i, j) == (0, 1) else "1 मटका = 3 kg" if (i, j) == (0, 2) else "?"
    s.text(lab, (x1 + x2) / 2, (y1 + y2) / 2, t0=t0 + 0.2, size=36 if lab != "?" else 34, style="pill", bg="#ffffff" if lab != "?" else "#e5484d", fill="#2b2b33" if lab != "?" else "#fff", z=25)
s.text("No common measure of value", 960, 960 - 60, t0=C("l17", "no common"), size=50, style="pill", bg="#2b2b33", fill="#fff", z=40)

# ---- 7 (l18) indivisibility
s = Shot("G", ["l18"], "haat", kicker="मुश्किल 3: Indivisibility")
mo = s.person("mohan", "mohan", 560, facing=1)
s.item(D_("charpai", 430), 880, FLOOR, t0=T.L("l18")["t0"] + 0.3)
st = s.person("saltman", "salt", 1500, facing=-1, t0=C("l18", "नमक") - 0.4)
s.pose(st, C("l18", "नमक"), "hold"); s.hold(st, C("l18", "नमक"), SALTP(90))
s.bubble(mo, SALTP(130), C("l18", "एक किलो"), w=230, dx=170, dy=-590)
s.arrow(880, 650, 880, 900, C("l18", "टुकड़े"), width=8, color="#e5484d", dashed=True, z=30)
s.item(D_("saw", 170), 880, 620, t0=C("l18", "टुकड़े"), z=31)
s.mark("cross", 880, 760, C("l18", "नहीं देगा"), w=200, z=40)
s.expr(mo, C("l18", "टुकड़े"), "sad")
s.text("Indivisibility of goods", 960, 200, t0=C("l18", "indivisibility"), size=60, style="pill", bg="#2b2b33", fill="#fff", z=50)

# ---- 8 (l19) storing wealth: grain spoils
s = Shot("H", ["l19"], "store", kicker="मुश्किल 4: Storing wealth")
sack = s.item(SACK("", w=360), 820, FLOOR, t0=T.L("l19")["t0"] + 0.3, keys=[{"t": C("l19", "नब्बे"), "d": 1.0, "s": 0.88}])
s.text("100 kg", 820, 560, t0=C("l19", "सौ किलो"), size=56, style="pill", bg="#f29f05", z=40, steps=[{"t": C("l19", "नब्बे"), "text": "90 kg"}])
s.item(D_("calendar", 210, text="1 महीना"), 1420, 640, t0=C("l19", "महीनों"), steps=None)
s.text("कुछ महीने बाद", 1420, 690, t0=C("l19", "महीनों") + 0.6, size=40, style="pill", bg="#e5484d", fill="#fff", z=42)
s.item({"draw": "bugs", "p": {"w": 330, "n": 12}, "anim": "t"}, 820, 760, t0=C("l19", "सड़"), z=30)
s.text("Difficulty in storing wealth", 960, 200, t0=C("l19", "difficulty"), size=60, style="pill", bg="#2b2b33", fill="#fff", z=50)

# ---- 9 (l20-l21) deferred payments
s = Shot("I", ["l20", "l21"], "haat", kicker="मुश्किल 5: Deferred payments")
ramu = s.person("ramu", "ramu", 620, facing=1)
mohan = s.person("mohan", "mohan", 1300, facing=-1)
s.pose(mohan, C("l20", "दो मीटर") - 0.6, "hold"); s.hold(mohan, C("l20", "दो मीटर") - 0.5, CLOTH(150))
s.give(CLOTH(150), mohan, ramu, C("l20", "दिया") - 0.2)
s.bubble(ramu, {"text": "अगली फ़सल पर 10 kg दूँगा", "size": 46, "style": "plain", "w": 360}, C("l20", "रामू"), t1=C("l21", frac=0.0) + 0.3, w=440, kind="speak", dx=230, dy=-600)
s.item(D_("calendar", 200, text="अगला साल"), 330, 470, t0=C("l21", "अगले साल"), z=30)
board = s.text("10 kg अनाज = 2 m कपड़ा", 960, 300, t0=C("l21", "सस्ता"), size=50, style="tag", z=45,
               steps=[{"t": C("l21", "सिर्फ़"), "text": "10 kg अनाज = सिर्फ़ 1 m कपड़ा"}])
s.pose(ramu, C("l21", "अगले साल") + 0.3, "hold"); s.hold(ramu, C("l21", "अगले साल") + 0.4, HSACK("10 kg", w=120))
s.give(HSACK("10 kg", w=120), ramu, mohan, C("l21", "सिर्फ़") + 0.8, keep=False, drop_to=(1170, FLOOR))
s.expr(mohan, C("l21", "घाटे"), "frown"); s.text("घाटा!", 1560, 430, t0=C("l21", "घाटे"), size=50, style="pill", bg="#e5484d", fill="#fff", z=55)
s.text("Deferred payments are difficult", 960, 180, t0=C("l21", "deferred"), size=56, style="pill", bg="#2b2b33", fill="#fff", z=60)

# ---- 10 (l22-l28) evolution of money: the book's six-step picture
s = Shot("J", ["l22", "l23", "l24", "l25", "l26", "l27", "l28"], "paper", kicker="Evolution of Money")
XS = [210 + i * 300 for i in range(6)]
LAB = ["1. Barter", "2. Commodity money", "3. Metallic money", "4. Paper money", "5. Bank money", "6. Digital money"]
COL = ["#f29f05", "#2fb463", "#c9a400", "#7b61ff", "#3a7bd5", "#e2558f"]
tb = T.L("l22")["t0"] + 0.2
s.text("पैसे का सफ़र: 6 कदम", 960, 170, t0=tb, t1=T.L("l23")["t0"], size=64, style="title", z=8)
for i, x in enumerate(XS):
    s.rect(x, 470, 270, 420, t0=tb + 0.3 + i * 0.25, z=1)
    s.text(LAB[i], x, 625, t0=tb + 0.3 + i * 0.25, size=28, style="pill", bg=COL[i], fill="#fff", w=210, z=4)
    s.text(str(i + 1), x - 105, 290, t0=tb + 0.3 + i * 0.25, size=30, style="pill", bg="#2b2b33", fill="#fff", z=4)
    if i < 5:
        s.arrow(x + 140, 470, x + 160, 470, tb + 0.4 + i * 0.25, width=8, z=6)
s.item(D_("wheat", 100), XS[0], 470, t0=tb + 0.5, z=3, t1=C("l23", "गेहूँ") + 0.3)
s.item(SALTP(100), XS[1], 500, t0=tb + 0.75, z=3, t1=C("l24", "नमक") + 0.3)
s.item(COIN("gold", 70), XS[2], 450, t0=tb + 1.0, z=3, t1=C("l25", "सोने") + 0.3)
s.item(NOTE(500, 210), XS[3], 450, t0=tb + 1.25, z=3, t1=C("l26", "नोट") + 0.3)
s.item(D_("bank", 210), XS[4], 540, t0=tb + 1.5, z=3, t1=C("l27", "bank", nth=2) + 0.3)
s.item(D_("phone", 100, screen="paid", amount="₹"), XS[5], 450, t0=tb + 1.75, z=3, t1=C("l28", "UPI") + 0.3)
ln = ["l23", "l24", "l25", "l26", "l27", "l28"]
x = XS[0]; t0 = T.L("l23")["t0"]
s.item({"draw": "__person__", "look": "ramu", "h": 190, "pose": "give", "facing": 1}, x - 55, 570, t0=t0, z=4)
s.item({"draw": "__person__", "look": "mohan", "h": 190, "pose": "give", "facing": -1}, x + 55, 570, t0=t0 + 0.1, z=4)
s.item(D_("wheat", 60), x - 50, 360, t0=C("l23", "गेहूँ"), z=5); s.item(CLOTH(70), x + 55, 360, t0=C("l23", "कपड़ा"), z=5)
x = XS[1]
s.item(SACK("नमक", "salt", w=110), x - 55, 420, t0=C("l24", "नमक"), z=4)
s.item(A("cow", 120), x + 50, 520, t0=C("l24", "मवेशी"), z=4)
s.item(D_("cowries", 34), x - 50, 560, t0=C("l24", "कौड़ियाँ"), z=5)
x = XS[2]
s.item(COIN("gold", 55), x - 45, 430, t0=C("l25", "सोने"), z=4); s.item(COIN("silver", 55), x + 45, 520, t0=C("l25", "चाँदी"), z=4)
x = XS[3]
s.item(D_("noteBundle", 190, value=500), x, 480, t0=C("l26", "नोट"), z=4)
x = XS[4]
s.item(D_("bank", 170), x, 470, t0=C("l27", "bank", nth=2), z=4); s.item(D_("cheque", 170), x, 560, t0=C("l27", "cheque"), z=5)
x = XS[5]
s.item(D_("phone", 85, screen="paid", amount="₹300"), x - 50, 470, t0=C("l28", "UPI"), z=4); s.item(A("credit_card", 100), x + 60, 540, t0=C("l28", "card"), z=5)
for i, lid in enumerate(ln):
    t0 = T.L(lid)["t0"] - 0.2
    s.camera(t0, max(XS[i], 600), 470, 1.6, 0.7)
s.camera(T.L("l28")["t1"] - 0.6, 960, 500, 1.0, 0.8)

# ---- 11 (l29) paper money at a shop: ₹500 given, ₹200 back
s = Shot("K", ["l29"], "shop", kicker="Paper money", fg="counter")
shop = s.person("shop", "shop", 1300, y=780, h=420, facing=-1, z=10)
ramu = s.person("ramu", "ramu", 430, y=920, h=460, facing=1, z=60)
s.item({"asset": "basket", "w": 190}, 960, 560, t0=C("l29", "सामान"), z=40)
s.text("₹300", 960, 430, t0=C("l29", "तीन सौ"), size=56, style="pill", bg="#f29f05", fill="#fff", z=45)
s.pose(ramu, C("l29", "पाँच सौ") - 0.5, "hold"); s.hold(ramu, C("l29", "पाँच सौ") - 0.4, NOTE(500, 150))
s.give(NOTE(500, 150), ramu, shop, C("l29", "देते"), z=70)
s.pose(shop, C("l29", "दो सौ") - 0.6, "hold"); s.hold(shop, C("l29", "दो सौ") - 0.5, {"group": [dict(NOTE(100, 130), x=-10, y=-12), dict(NOTE(100, 130), x=10, y=8)]})
s.give({"group": [dict(NOTE(100, 130), x=-10, y=-12), dict(NOTE(100, 130), x=10, y=8)]}, shop, ramu, C("l29", "वापस"), z=70)
s.text("₹500 − ₹300 = ₹200 वापस", 960, 250, t0=C("l29", "वापस") + 0.3, size=50, style="tag", z=50)
s.text("Paper money", 960, 140, t0=C("l29", "paper"), size=64, style="title", z=50)

# ---- 12 (l30) bank money: cheque, accounts change
s = Shot("L", ["l30"], "paper", kicker="Bank money")
s.item({"draw": "__person__", "look": "ramu", "h": 440, "pose": "write", "facing": 1}, 240, 900, t0=C("l30", "cheque"))
chq = s.item(D_("cheque", 300, amount="₹1,500"), 470, 470, t0=C("l30", "cheque") + 0.2, z=30,
             keys=[{"t": C("l30", "bank"), "d": 1.0, "x": 900, "y": 470, "s": 0.8}])
s.item(D_("bank", 420), 900, 860, t0=C("l30", "bank"), z=10)
r_acc = s.item(D_("accountCard", 380, title="रामू का खाता", amount=""), 1500, 330, t0=C("l30", "आपके खाते"), z=20)
s.text("₹10,000", 1500, 355, t0=C("l30", "आपके खाते"), size=56, style="plain", z=25, steps=[{"t": C("l30", "निकालकर"), "text": "₹8,500"}])
s.item(D_("accountCard", 380, title="दुकानदार का खाता", amount="", color="#2fb463"), 1500, 720, t0=C("l30", "दुकानदार"), z=20)
s.text("₹2,000", 1500, 745, t0=C("l30", "दुकानदार"), size=56, style="plain", z=25, steps=[{"t": C("l30", "डाल"), "text": "₹3,500"}])
s.arrow(1500, 440, 1500, 600, C("l30", "डाल") - 0.5, width=12, color="#2fb463", z=30)
s.text("−₹1,500", 1700, 520, t0=C("l30", "निकालकर"), size=40, style="pill", bg="#e5484d", fill="#fff", z=35)
s.text("Bank money", 960, 140, t0=C("l30", "bank money"), size=64, style="title", z=50)

# ---- 13 (l31) digital money: QR scan
s = Shot("M", ["l31"], "shop", kicker="Digital money", fg="counter")
shop = s.person("shop", "shop", 1250, y=780, h=420, facing=-1, z=10)
ramu = s.person("ramu", "ramu", 560, y=920, h=460, facing=1, z=60)
s.item(D_("qrStand", 170), 960, 650, t0=C("l31", "QR"), z=40)
tq = C("l31", "QR")
s.pose(ramu, tq - 0.4, "point")
s.hold(ramu, tq - 0.3, {"draw": "phone", "p": {"w": 90, "screen": "scan"}, "anim": "p", "pt": tq, "pd": 1.6})
s.hold(ramu, C("l31", "तीन सौ"), {"draw": "phone", "p": {"w": 90, "screen": "paid", "amount": "₹300"}})
s.camera(tq - 0.3, 860, 560, 1.7, 0.7)
s.camera(C("l31", "तीन सौ") + 0.8, 1150, 520, 1.6, 0.8)
s.pose(shop, C("l31", "भेजे"), "hold"); s.hold(shop, C("l31", "भेजे"), {"draw": "phone", "p": {"w": 90, "screen": "received", "amount": "₹300"}})
s.camera(C("l31", "पैसा"), 960, 540, 1.0, 0.8)
yy = 260
s.item(D_("bank", 200, label="रामू का बैंक"), 600, yy + 90, t0=C("l31", "खाते"), z=45)
s.item(D_("bank", 200, label="दुकान का बैंक"), 1320, yy + 90, t0=C("l31", "खाते") + 0.2, z=45)
s.arrow(720, yy, 1200, yy, C("l31", "खाते") + 0.5, width=12, color="#2fb463", z=46)
s.text("₹300", 960, yy - 40, t0=C("l31", "खाते") + 0.8, size=44, style="pill", bg="#2fb463", fill="#fff", z=47)
s.text("phone से हुक्म", 960, 430, t0=C("l31", "हुक्म"), size=44, style="pill", bg="#7b61ff", fill="#fff", z=47)

# ---- 14 (l32-l34) where does value come from: salt vs note
s = Shot("N", ["l32", "l33", "l34"], "paper", kicker="क़ीमत कहाँ से?")
s.text("पैसे की क़ीमत कहाँ से आती है?", 960, 170, t0=C("l32", "क़ीमत"), size=62, style="title", z=50)
salt = s.item(SALTP(170), 480, 560, t0=C("l32", frac=0.0), z=20, keys=[{"t": C("l33", "खाने"), "d": 0.9, "x": 560, "y": 500, "s": 0.6}])
s.item(A("pot_of_food", 240), 560, 650, t0=C("l33", "खाने"), z=15)
s.mark("tick", 360, 400, C("l33", "काम आएगा"), w=110)
s.text("Intrinsic value: अपनी चीज़ की क़ीमत", 480, 860, t0=C("l33", "intrinsic"), size=44, style="pill", bg="#2fb463", fill="#fff", w=700, z=40)
note = s.item(NOTE(500, 300), 1440, 520, t0=C("l32", frac=0.0) + 0.2, z=20)
s.text("सिर्फ़ काग़ज़ ≈ कुछ नहीं", 1440, 360, t0=C("l34", "काग़ज़"), t1=C("l34", "सरकार"), size=40, style="pill", bg="#9a9aa6", fill="#fff", z=40)
s.item(A("classical_building", 150), 1240, 700, t0=C("l34", "सरकार"), z=21)
s.item(A("balance_scale", 140), 1440, 720, t0=C("l34", "क़ानून"), z=21)
s.item(A("handshake", 140), 1640, 700, t0=C("l34", "भरोसा"), z=21)
s.text("Extrinsic value: सरकार, क़ानून, भरोसा", 1440, 860, t0=C("l34", "extrinsic"), size=44, style="pill", bg="#7b61ff", fill="#fff", w=700, z=40)
s.mark("question", 960, 520, C("l32", "कहाँ"), t1=C("l33", frac=0.0), w=160)

# ---- 15 (l35-l45) intrinsic vs extrinsic, ten differences one by one
s = Shot("O", ["l35", "l36", "l37", "l38", "l39", "l40", "l41", "l42", "l43", "l44", "l45"], "paper", kicker="Intrinsic vs Extrinsic")
s.rect(480, 170, 760, 150, t0=C("l35", frac=0.0), z=1, fill="#e7f6ec"); s.rect(1440, 170, 760, 150, t0=C("l35", frac=0.0), z=1, fill="#efebff")
s.item(COIN("gold", 45), 170, 170, z=3, t0=C("l35", frac=0.0)); s.item(SALTP(60), 260, 205, z=3, t0=C("l35", frac=0.0))
s.text("Intrinsic (अपनी क़ीमत)", 590, 170, t0=C("l35", frac=0.0), size=46, style="plain", z=3)
s.item(NOTE(500, 120), 1150, 170, z=3, t0=C("l35", frac=0.0)); s.item(D_("phone", 45, screen="paid", amount="₹"), 1250, 175, z=3, t0=C("l35", frac=0.0))
s.text("Extrinsic (बाहरी भरोसा)", 1560, 170, t0=C("l35", frac=0.0), size=46, style="plain", z=3)
s.arrow(960, 110, 960, 900, C("l35", frac=0.0), width=4, color="#c9bfa8", z=0, dashed=True)
t35 = T.L("l35")["t0"]
s.text("10 फ़र्क", 960, 520, t0=t35 + 0.2, t1=T.L("l36")["t0"] - 0.2, size=110, style="plain", fill="#7b61ff", z=10)
for k in range(10):
    s.add({"kind": "glow", "x": 735 + k * 50, "y": 650, "w": 30, "t0": t35 + 0.5 + k * 0.12, "t1": T.L("l36")["t0"] - 0.2, "z": 10, "fill": "#7b61ff"})
ROWS = [
 ("l36", "1. आधार", [A("leaf_fluttering_in_wind", 150), dict(D_("goldBar", 170), y=40)], "Natural", [A("handshake", 150), A("balance_scale", 150)], "भरोसा + क़ानून"),
 ("l37", "2. क़ीमत का स्रोत", [dict(D_("goldBar", 240), y=60)], "अपना material", [A("classical_building", 220)], "सरकार की backing"),
 ("l38", "3. Inherent worth", [COIN("gold", 80), {"draw": "mark", "p": {"kind": "tick", "w": 140}}], "है", [NOTE(500, 230), {"draw": "mark", "p": {"kind": "cross", "w": 140}}], "नहीं"),
 ("l39", "4. पैसा न चले तो?", [COIN("gold", 70), A("shopping_bags", 130)], "फिर भी बिकेगा", [NOTE(500, 200), {"text": "काग़ज़", "size": 44, "style": "pill", "bg": "#9a9aa6", "fill": "#fff"}], "क़ीमत nil"),
 ("l40", "5. उदाहरण", [COIN("gold", 50), COIN("silver", 50), dict(SACK("नमक", "salt", w=110), y=50), A("cow", 120), dict(D_("cowries", 30), y=30)], "सोना, चाँदी, नमक, मवेशी, कौड़ियाँ",
  [NOTE(500, 150), dict(D_("bank", 140), y=60), D_("phone", 60, screen="paid", amount="₹")], "नोट, bank deposit, digital"),
 ("l41", "6. कितने लोग लेते हैं", [{"group": [mini("villager", h=150, x=-120), mini("sita", h=150, x=-40), mini("raju", h=150, x=40), mini("oil", h=150, x=120)], "y": 70}], "कुछ हद तक",
  [{"group": [mini("villager", h=150, x=-120), mini("sita", h=150, x=-40), mini("raju", h=150, x=40), mini("oil", h=150, x=120)], "y": 70}], "सब (legal tender)"),
 ("l42", "7. टिकाऊपन", [COIN("gold", 80)], "आमतौर पर टिकता", [NOTE(500, 200), D_("phone", 70, screen="home")], "फटता / technology पर"),
 ("l43", "8. बाँटना", [dict(D_("goldBar", 230), y=40)], "मुश्किल", [NOTE(100, 170), NOTE(50, 120), NOTE(50, 120)], "आसान"),
 ("l44", "9. ढोना", [dict(SACK("", w=120), y=60), dict(D_("goldBar", 120), y=40)], "भारी, मुश्किल", [NOTE(500, 150), D_("phone", 60, screen="home")], "जेब में, आसान"),
 ("l45", "10. आज के उदाहरण", [{"draw": "coinStack", "p": {"r": 45, "n": 5}}, dict(D_("goldBar", 150), y=30)], "सिक्के, सोने की ईंटें",
  [NOTE(500, 150), D_("accountCard", 200, title="Bank balance", amount="₹"), D_("phone", 60, screen="paid", amount="UPI")], "नोट, bank balance, UPI"),
]
for lid, title, lv, lt, rv, rt in ROWS:
    t0, t1 = T.L(lid)["t0"] - 0.2, T.L(lid)["t1"] + 0.35
    s.text(title, 960, 330, t0=t0, t1=t1, size=48, style="pill", bg="#2b2b33", fill="#fff", z=30)
    for side, vis, lab, x0 in (("L", lv, lt, 480), ("R", rv, rt, 1440)):
        n = len(vis); gap = 680 / max(1, n)
        ts = t0 + (0.2 if side == "L" else T.L(lid)["t0"] + (T.L(lid)["t1"] - T.L(lid)["t0"]) * 0.5 - t0)
        for k, v in enumerate(vis):
            xx = x0 - 340 + gap * (k + 0.5)
            vv = dict(v); oy = vv.pop("y", 0)
            s.item({"group": [dict(vv, y=oy)]}, xx, 580, t0=ts + k * 0.15, t1=t1, z=20, s=1.5 if n <= 2 else 1.25)
        s.text(lab, x0, 800, t0=ts + 0.3, t1=t1, size=46, style="tag", w=640, z=25)
# ticks in row 6 (who accepts)
r6 = T.L("l41")
for k, xx in enumerate([360, 440]):
    s.mark("tick", xx, 470, r6["t0"] + 1.2, t1=r6["t1"] + 0.35, w=60)
for k in range(4):
    s.mark("tick", 1320 + k * 80, 470, r6["t0"] + (r6["t1"] - r6["t0"]) * 0.6 + k * 0.1, t1=r6["t1"] + 0.35, w=60)
r8 = T.L("l43")
s.arrow(480, 470, 480, 690, r8["t0"] + 1.0, t1=r8["t1"] + 0.35, width=7, color="#e5484d", dashed=True, z=40)
s.mark("cross", 600, 520, r8["t0"] + 1.6, t1=r8["t1"] + 0.35, w=90)
s.mark("tick", 1700, 500, r8["t0"] + (r8["t1"] - r8["t0"]) * 0.75, t1=r8["t1"] + 0.35, w=90)
r9 = T.L("l44")
s.item(D_("sweat", 40), 560, 470, t0=r9["t0"] + 1.0, t1=r9["t1"] + 0.35, z=40)

# ---- 16 (l46-l51) commodity money story: salt becomes the bridge
s = Shot("P", ["l46", "l47", "l48", "l49", "l50", "l51"], "haat", kicker="Commodity money")
s.text("Commodity money", 960, 170, t0=C("l46", "commodity"), t1=C("l47", frac=0.0) + 1.0, size=80, style="title", z=60)
ramu = s.person("ramu", "ramu", 380, facing=1, t0=C("l47", frac=0.0), z=15)
s.pose(ramu, C("l47", frac=0.0), "hold"); s.hold(ramu, C("l47", frac=0.0), HSACK("गेहूँ", w=110))
saltm = s.person("saltman", "salt", 940, facing=-1, t0=C("l47", "नमक") - 0.3)
s.item(SACK("नमक", "salt", w=170), 1100, FLOOR, t0=C("l47", "नमक") - 0.3)
mohan = s.person("mohan", "mohan", 1560, facing=-1, t0=C("l47", "मोहन"))
s.item(D_("clothStack", 160), 1760, FLOOR, t0=C("l47", "मोहन"))
s.bubble(ramu, CLOTH(160), C("l47", "कपड़ा"), w=220, dx=170, dy=-580, t1=C("l48", frac=0.0))
b1 = s.bubble(mohan, D_("wheat", 120), C("l47", "गेहूँ"), w=220, dx=-170, dy=-580, t1=C("l47", "मोहन को नमक"))
s.mark("cross", 1390, 330, C("l47", "नहीं चाहिए"), t1=C("l47", "मोहन को नमक"), w=130)
s.bubble(mohan, SALTP(110), C("l47", "मोहन को नमक"), w=220, dx=-170, dy=-580, t1=C("l48", frac=0.0))
for k, (look, xx) in enumerate([("villager", 700), ("sita", 1230), ("oil", 1400)]):
    pv = s.person(f"v{k}", look, xx, y=720, h=230, facing=1 if k == 0 else -1, t0=C("l47", "सब लेते") + k * 0.15, t1=C("l48", frac=0.0) + 0.5, z=2)
    pv["nods"].append({"t": C("l47", "सब लेते") + 0.3, "d": 1.2})
t_a = C("l48", "गेहूँ देकर")
s.give(HSACK("गेहूँ", w=110), ramu, saltm, t_a, keep=False, drop_to=(1040, FLOOR))
s.pose(saltm, C("l48", "नमक लेता") - 0.7, "hold"); s.hold(saltm, C("l48", "नमक लेता") - 0.6, SALTP(90))
s.give(SALTP(90), saltm, ramu, C("l48", "नमक लेता") - 0.1)
s.walk(ramu, C("l48", "फिर") - 0.2, 1180, 1.4)
s.give(SALTP(90), ramu, mohan, C("l48", "मोहन को"), keep=True)
s.pose(mohan, C("l48", "कपड़ा") - 0.3, "hold")
s.give(CLOTH(150), mohan, ramu, C("l48", "कपड़ा ले") + 0.3)
s.expr(ramu, C("l48", "कपड़ा ले") + 1.0, "happy"); s.expr(mohan, C("l48", "कपड़ा ले") + 1.0, "happy")
tb = C("l49", "पुल")
s.rect(960, 245, 1240, 330, t0=tb - 0.2, z=55)
s.item(mini("ramu", h=150), 470, 340, t0=tb, z=56); s.item(mini("mohan", h=150, facing=-1), 1450, 340, t0=tb, z=56)
s.arrow(540, 200, 1380, 200, tb + 0.2, width=12, bend=-0.08, color="#f29f05", z=56)
s.item(SALTP(80), 960, 160, t0=tb + 0.5, z=57)
s.text("Medium of exchange = बीच का पुल", 960, 255, t0=C("l49", "medium"), size=44, style="pill", bg="#f29f05", fill="#fff", z=58)
s.text("Double coincidence की ज़रूरत", 960, 345, t0=C("l49", "अब"), size=40, style="plain", fill="#e5484d", z=58)
s.mark("cross", 960, 345, C("l49", "नहीं रही"), w=140, z=59)
t50 = T.L("l50")["t0"] - 0.2
s.rect(960, 520, 1920, 1080, t0=t50, z=80, fill="#f7f1e5", shadow=False, alpha=0.96)
s.item(SALTP(190), 520, 600, t0=t50 + 0.2, z=81)
s.text("पैसे का काम ✓", 1120, 420, t0=C("l50", "पैसे"), size=56, style="tag", z=82)
s.text("अपनी भी क़ीमत ✓", 1120, 560, t0=C("l50", "अपनी"), size=56, style="tag", z=82)
s.text("= Commodity money", 1120, 720, t0=C("l50", "commodity"), size=64, style="pill", bg="#2fb463", fill="#fff", z=82)
s.item(A("pot_of_food", 220), 520, 640, t0=C("l51", "खाने"), z=83, keys=[])
s.text("Intrinsic value", 520, 820, t0=C("l51", "intrinsic"), size=48, style="pill", bg="#7b61ff", fill="#fff", z=84)

# ---- 17 (l52-l56) where things became money: map with pins
s = Shot("Q", ["l52", "l53", "l54", "l55", "l56"], "parchment", kicker="कहाँ क्या पैसा बना")
MAP = json.load(open("dist/map.json"))["pins"]
s.add({"kind": "map", "x": 0, "y": 0, "t0": s.t0, "z": 1, "enter": "fade"})
def pin(key, label, spec, t0, dx=110, dy=-40):
    x, y = MAP[key]
    s.add({"kind": "glow", "x": x, "y": y, "w": 70, "t0": t0, "z": 5, "fill": "#e5484d"})
    s.mark("circle", x, y, t0, w=34, z=6, color="#e5484d")
    s.text(label, x, y + 45, t0=t0 + 0.2, size=34, style="pill", bg="#2b2b33", fill="#fff", z=8)
    s.item(spec, x + dx, y + dy, t0=t0 + 0.3, z=7)
pin("rome", "Ancient Rome", SALTP(70), C("l52", "rome"), dx=-90)
pin("africa", "Africa", SACK("नमक", "salt", w=90), C("l52", "africa"), dx=110, dy=0)
s.camera(C("l52", frac=0.0), 1000, 420, 1.6, 0.9)
s.camera(C("l53", frac=0.0) - 0.2, 960, 540, 1.0, 0.7)
t53 = T.L("l53")["t0"]
s.rect(960, 560, 1100, 640, t0=t53, t1=T.L("l53")["t1"] + 0.3, z=20, fill="#fdf6e3")
hd = s.person("herder", "herder", 700, y=820, h=360, facing=1, t0=t53 + 0.2, t1=T.L("l53")["t1"] + 0.3, z=21)
s.item(A("cow", 200), 1000, 720, t0=C("l53", "मवेशी"), t1=T.L("l53")["t1"] + 0.3, z=21)
s.item(A("ox", 200), 1220, 730, t0=C("l53", "मवेशी") + 0.2, t1=T.L("l53")["t1"] + 0.3, z=21)
s.item(A("goat", 140), 1330, 800, t0=C("l53", "जानवर"), t1=T.L("l53")["t1"] + 0.3, z=21)
s.text("Early pastoral societies", 960, 330, t0=C("l53", "early"), t1=T.L("l53")["t1"] + 0.3, size=52, style="pill", bg="#2fb463", fill="#fff", z=22)
pin("india", "India", D_("cowries", 30), C("l54", "भारत"), dx=0, dy=-110)
pin("china", "China", D_("cowries", 30), C("l54", "चीन"), dx=110, dy=-20)
s.text("कौड़ियाँ", MAP["africa"][0], MAP["africa"][1] + 110, t0=C("l54", "Africa"), size=34, style="pill", bg="#f29f05", fill="#fff", z=8)
s.camera(C("l54", frac=0.0), 1250, 470, 1.5, 0.9)
pin("central_asia", "Central Asia", D_("teaBrick", 90), C("l55", "central"), dx=-110, dy=-60)
pin("tibet", "Tibet", D_("teaBrick", 90), C("l55", "tibet"), dx=60, dy=-120)
s.camera(C("l55", frac=0.0), 1280, 420, 1.9, 0.9)
pin("colonial_america", "Colonial America", D_("tobacco", 120), C("l56", "colonial"), dx=-130, dy=-60)
s.camera(C("l56", frac=0.0) - 0.2, 600, 420, 1.7, 0.9)
s.camera(T.L("l56")["t1"] - 0.2, 960, 520, 1.0, 1.0)

# ---- 18 (l57-l60) features of commodity money
s = Shot("R", ["l57", "l58", "l59", "l60"], "paper", kicker="Commodity money की ख़ूबियाँ")
feat2 = [("l57", "अपनी क़ीमत, इसलिए barter से ज़्यादा भरोसा"), ("l58", "पूरा समाज मानता: widely accepted"),
         ("l59", "लेन-देन के अलावा भी काम आता"), ("l60", "सिक्कों से पहले बीच का पुल")]
for i, ((cx, cy), (lid, txt)) in enumerate(zip(CARDS, feat2)):
    t0 = T.L(lid)["t0"]
    s.rect(cx, cy, 860, 360, t0=t0, z=1)
    s.text(str(i + 1), cx - 385, cy - 135, t0=t0, size=40, style="pill", bg="#2fb463", z=3)
    s.text(txt, cx + 190, cy, t0=t0 + 0.3, size=46, style="plain", w=440, z=3)
    s.camera(t0 - 0.2, cx, cy, 1.55, 0.7)
cx, cy = CARDS[0]; t0 = T.L("l57")["t0"]
s.item(SALTP(120), cx - 280, cy + 60, t0=t0 + 0.2, z=4); s.mark("tick", cx - 150, cy - 50, C("l57", "आसानी"), w=90, z=5)
cx, cy = CARDS[1]; t0 = T.L("l58")["t0"]
s.item(SALTP(80), cx - 230, cy - 60, t0=t0 + 0.2, z=4)
for k in range(5):
    s.item(mini(["villager", "sita", "raju", "oil", "mohan"][k], h=140), cx - 370 + k * 70, cy + 140, t0=t0 + 0.3 + k * 0.1, z=4)
    s.mark("tick", cx - 370 + k * 70, cy - 10, C("l58", "widely") + k * 0.08, w=40, z=5)
cx, cy = CARDS[2]; t0 = T.L("l59")["t0"]
s.item(SALTP(80), cx - 340, cy - 20, t0=t0 + 0.3, z=4); s.item(A("pot_of_food", 110), cx - 220, cy + 70, t0=C("l59", "खाने"), z=4)
s.item(A("cow", 120), cx - 330, cy + 120, t0=t0 + 0.5, z=4); s.item(A("bucket", 80), cx - 200, cy - 80, t0=C("l59", "दूध"), z=4)
cx, cy = CARDS[3]; t0 = T.L("l60")["t0"]
s.item(mini("ramu", h=150), cx - 380, cy + 130, t0=t0 + 0.2, z=4); s.item(mini("mohan", h=150, facing=-1), cx - 80, cy + 130, t0=t0 + 0.2, z=4)
s.arrow(cx - 360, cy - 10, cx - 100, cy - 10, C("l60", "medium"), width=9, bend=-0.3, color="#f29f05", z=4)
s.item(SALTP(60), cx - 230, cy - 90, t0=C("l60", "medium") + 0.3, z=5)
s.camera(T.L("l60")["t1"] - 0.3, 960, 520, 1.0, 0.8)

# ---- 19 (l61-l65) limitations of commodity money
s = Shot("S", ["l61", "l62", "l63", "l64", "l65"], "paper", kicker="Commodity money की मुश्किलें")
LC = [(340, 330), (960, 330), (1580, 330), (650, 735), (1270, 735)]
lim = [("l61", "Lack of uniformity"), ("l62", "Poor divisibility"), ("l63", "Perishable"), ("l64", "Difficult transport"), ("l65", "Limited standardization")]
for i, ((cx, cy), (lid, en)) in enumerate(zip(LC, lim)):
    t0 = T.L(lid)["t0"]
    s.rect(cx, cy, 580, 380, t0=t0, z=1)
    s.text(en, cx, cy + 140, t0=C(lid, en.split()[0].lower() if en.split()[0].lower() in T.L(lid)["sub"] else None) if False else t0 + 0.4, size=40, style="pill", bg="#e5484d", fill="#fff", z=3)
    s.camera(t0 - 0.2, cx, cy, 1.6, 0.7)
cx, cy = LC[0]
s.item(D_("heap", 170, kind="salt"), cx - 130, cy + 60, t0=T.L("l61")["t0"] + 0.3, z=4)
s.item(D_("heap", 170, kind="salt", wet=True), cx + 130, cy + 60, t0=C("l61", "गीला"), z=4)
s.text("≠", cx, cy - 10, t0=C("l61", "गीला") + 0.3, size=90, style="plain", fill="#e5484d", z=5)
cx, cy = LC[1]
s.item(D_("teaBrick", 200, crack=True), cx, cy + 60, t0=T.L("l62")["t0"] + 0.3, z=4); s.mark("cross", cx + 150, cy - 40, C("l62", "आसान नहीं"), w=100, z=5)
cx, cy = LC[2]
s.item(D_("heap", 150, kind="salt", wet=True), cx - 120, cy + 60, t0=T.L("l63")["t0"] + 0.3, z=4)
s.item(D_("heap", 150, kind="grain"), cx + 120, cy + 60, t0=T.L("l63")["t0"] + 0.5, z=4)
s.item({"draw": "bugs", "p": {"w": 160, "n": 7}, "anim": "t"}, cx + 120, cy + 20, t0=C("l63", "सड़"), z=5)
cx, cy = LC[3]
pp = s.person("carrier", "herder", cx - 60, y=cy + 110, h=300, facing=1, t0=T.L("l64")["t0"], z=4)
s.pose(pp, T.L("l64")["t0"], "carry"); s.hold(pp, T.L("l64")["t0"], dict(SACK("", w=130), y=40))
s.expr(pp, T.L("l64")["t0"] + 0.5, "sad"); s.item(D_("sweat", 30), cx + 30, cy - 160, t0=C("l64", "मुश्किल"), z=6)
s.item(SACK("", w=120), cx + 140, cy + 100, t0=C("l64", "बोरियाँ"), z=4)
cx, cy = LC[4]
s.item(A("balance_scale", 150), cx - 150, cy + 10, t0=T.L("l65")["t0"] + 0.3, z=4)
s.item(A("magnifying_glass_tilted_left", 110), cx + 10, cy - 10, t0=C("l65", "जाँचो"), z=4)
s.text("?", cx + 160, cy - 60, t0=C("l65", "मोल"), size=70, style="tag", z=5)
s.text("?", cx + 200, cy + 30, t0=C("l65", "मोल") + 0.2, size=60, style="tag", z=5)
s.camera(T.L("l65")["t1"] - 0.3, 960, 520, 1.0, 0.8)

# ---- 20 (l66-l67) recap and what comes next
s = Shot("U", ["l66", "l67"], "paper", kicker="याद रखिए")
t0 = T.L("l66")["t0"]
s.rect(500, 450, 820, 560, t0=t0, z=1); s.rect(1420, 450, 820, 560, t0=C("l66", "commodity"), z=1)
s.text("Barter", 500, 230, t0=t0, size=54, style="pill", bg="#f29f05", fill="#fff", z=3)
s.item(mini("ramu", h=220), 330, 640, t0=t0 + 0.2, z=3); s.item(mini("mohan", h=220, facing=-1), 670, 640, t0=t0 + 0.2, z=3)
s.item(D_("wheat", 70), 430, 420, t0=C("l66", "चीज़"), z=4); s.item(CLOTH(80), 570, 420, t0=C("l66", "चीज़") + 0.2, z=4)
s.arrow(390, 470, 610, 470, C("l66", "चीज़") + 0.3, width=8, bend=-0.3, color="#2fb463", z=4)
s.text("चीज़ ⇄ चीज़", 500, 670, t0=C("l66", "चीज़") + 0.4, size=46, style="tag", z=4)
tc = C("l66", "commodity")
s.text("Commodity money", 1420, 230, t0=tc, size=54, style="pill", bg="#2fb463", fill="#fff", z=3)
s.item(mini("ramu", h=220), 1180, 640, t0=tc + 0.2, z=3); s.item(mini("salt", h=220, facing=-1), 1420, 640, t0=tc + 0.3, z=3); s.item(mini("mohan", h=220, facing=-1), 1660, 640, t0=tc + 0.4, z=3)
s.arrow(1200, 420, 1640, 420, C("l66", "पुल"), width=10, bend=-0.25, color="#f29f05", z=4)
s.item(SALTP(70), 1420, 330, t0=C("l66", "पुल") + 0.3, z=5)
s.text("बीच का पुल, अपनी क़ीमत वाला", 1420, 690, t0=C("l66", "पुल") + 0.4, size=42, style="tag", w=700, z=4)
t67 = T.L("l67")["t0"]
s.rect(960, 540, 1920, 1080, t0=t67, z=80, fill="#2b2b33", shadow=False, alpha=0.92)
s.item(COIN("gold", 120), 800, 520, t0=C("l67", "धातु"), z=81); s.item(COIN("silver", 120), 1100, 520, t0=C("l67", "धातु") + 0.2, z=81)
s.add({"kind": "glow", "x": 950, "y": 520, "w": 520, "t0": C("l67", "धातु"), "z": 80.5, "fill": "#ffd95a"})
s.text("अगला: Metallic money", 960, 780, t0=C("l67", "अगले"), size=64, style="pill", bg="#f29f05", fill="#fff", z=82)

# ================================================================= write
for i, sh in enumerate(SHOTS):
    sh.t1 = SHOTS[i + 1].t0 if i + 1 < len(SHOTS) else T.duration
if SHOTS:
    SHOTS[0].t0 = 0.0
spec = {"fps": 30, "width": int(sys.argv[2]) if len(sys.argv) > 2 else 1280, "height": int(sys.argv[3]) if len(sys.argv) > 3 else 720,
        "duration": round(T.duration, 3), "subs": T.subs(),
        "scenes": [{"id": sh.id, "t0": round(sh.t0, 3), "t1": round(sh.t1, 3), "bg": sh.bg, "fg": sh.fg, "kicker": sh.kicker, "cam": sh.cam,
                    "els": [e for e in sh.els if e.get("h", 1) != 0]} for sh in SHOTS]}
json.dump(spec, open(sys.argv[1] if len(sys.argv) > 1 else "spec.json", "w"), ensure_ascii=False)
print("shots", len(SHOTS), "elements", sum(len(x["els"]) for x in spec["scenes"]), "duration", round(T.duration, 1), "estimated parts", T.estimated)
