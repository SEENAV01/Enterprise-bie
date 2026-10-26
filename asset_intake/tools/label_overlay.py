"""Draw code labels with leader lines on a recipe preview, from the anchors the recipe reported.

This shows how BIE puts text on top of a render: the render has no text; the recipe reports where each part is on
screen, and code draws the label in any language. Usage:
    python label_overlay.py PREVIEW.png OUT.png [--side right|left] [--title "..."]
Labels come from PREVIEW.png.json ("anchors": {name: [x, y]}); "anchor_" prefixes are stripped.
"""
import argparse
import json

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("preview")
    p.add_argument("out")
    p.add_argument("--side", default="right")
    p.add_argument("--title", default="")
    p.add_argument("--rename", default="", help='JSON map of anchor name -> label text')
    a = p.parse_args()
    rec = json.load(open(a.preview + ".json"))
    rename = json.loads(a.rename) if a.rename else {}
    im = Image.open(a.preview).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, max(14, H // 34))
    ft = ImageFont.truetype(FONT, max(16, H // 26))
    anchors = [(rename.get(k, k.replace("anchor_", "").replace("_", " ")), v) for k, v in rec.get("anchors", {}).items() if v]
    anchors.sort(key=lambda kv: kv[1][1])
    n = len(anchors)
    for i, (label, (x, y)) in enumerate(anchors):
        ly = int(H * 0.18 + i * (H * 0.64) / max(1, n - 1)) if n > 1 else int(y)
        tw = d.textlength(label, font=f)
        lx = int(W * 0.80) if a.side == "right" else int(W * 0.04)
        bx0, bx1 = (lx, lx + tw + 20) if a.side == "right" else (lx, lx + tw + 20)
        elbow = bx0 - 30 if a.side == "right" else bx1 + 30
        d.line([(x, y), (elbow, ly), (bx0 if a.side == "right" else bx1, ly)], fill=(255, 214, 92), width=2)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 214, 92))
        d.rounded_rectangle([bx0, ly - 16, bx1, ly + 16], radius=8, fill=(10, 16, 28), outline=(255, 214, 92), width=2)
        d.text((bx0 + 10, ly - 11), label, font=f, fill=(255, 255, 255))
    if a.title:
        d.rounded_rectangle([16, 14, 26 + d.textlength(a.title, font=ft), 52], radius=8, fill=(10, 16, 28))
        d.text((21, 19), a.title, font=ft, fill=(120, 230, 220))
    im.save(a.out)


if __name__ == "__main__":
    main()
