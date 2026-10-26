"""Compact helpers to write shot cards (same schema as the Gemini prompt) from frame review.

C(rng, teaches, level, objs, proc, cam, look, labels, label_style, formula, notes)
  rng      "m:ss-m:ss" (a card may cover several consecutive code-detected shots of one scene)
  objs     list of "name|kind|dim|style|detail|change"
  proc     "what_moves > from > to" (cause/effect optional after ' || ')
  cam      "size angle movement transition"
  look     "background ; palette csv ; lighting ; effects csv"
"""
import json


def _t(s):
    m, x = s.split(":")
    return int(m) * 60 + int(x)


def C(rng, teaches, level, objs=(), proc="", cam="medium 30deg-above static cut", look="", labels=(),
      label_style="none", formula=False, recipe=(), notes=""):
    a, b = rng.split("-")
    objects = []
    for o in objs:
        p = (o.split("|") + [""] * 6)[:6]
        objects.append({"name": p[0], "kind": p[1], "dim": p[2], "style": p[3], "detail": p[4], "change": p[5]})
    pm, _, ce = proc.partition(" || ")
    pp = ([x.strip() for x in pm.split(">")] + ["", "", ""])[:3] if pm else ["", "", ""]
    cause, _, effect = ce.partition(" => ")
    cs = (cam.split() + ["", "", "", ""])[:4]
    lk = ([x.strip() for x in look.split(";")] + ["", "", "", ""])[:4]
    return {"start": a, "end": b, "seconds": _t(b) - _t(a), "teaches": teaches, "level": level,
            "objects": objects,
            "process": {"what_moves": pp[0], "from": pp[1], "to": pp[2], "cause": cause.strip(), "effect": effect.strip()},
            "camera": {"size": cs[0], "angle": cs[1], "movement": cs[2], "transition_in": cs[3]},
            "look": {"background": lk[0], "palette": [x.strip() for x in lk[1].split(",") if x.strip()],
                     "lighting": lk[2], "effects": [x.strip() for x in lk[3].split(",") if x.strip()]},
            "on_screen_text": {"labels": list(labels), "label_style": label_style, "formula": formula},
            "recipe_needs": list(recipe), "notes": notes}


def video(id, title, channel, subject, topic, audience, overall, analysed, style, cards, source="frames+code"):
    return {"id": id, "title": title, "channel": channel, "subject": subject, "topic": topic,
            "audience_level": audience, "overall_level": overall, "analysed_range": analysed,
            "seen_visuals": True, "method": source, "style_summary": style, "shots": cards}


def save(v, path):
    json.dump(v, open(path, "w"), ensure_ascii=False, indent=1)
