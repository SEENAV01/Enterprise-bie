"""Talmel sheets: what was SAID when each thing APPEARED (teaching-showing fit), for one video.

For up to N visual change events (adds and big changes, spread over the video), one tile = the frame just after the
change with a red box around the changed area, and under it the words spoken from 3 s before to 1.5 s after the
change (word timings from stt2/<ID>.json), the word nearest the change in brackets. 3 x 4 tiles per sheet.
Writes talmel/<ID>/sheet-NN.jpg and talmel/<ID>/tiles.json. Usage: talmel_sheets.py ID [N]
"""
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

B = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(B), "v2demo", "dist", "fonts")
vid = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 24
f = os.path.join(B, "vids", vid + ".mp4")
ev = json.load(open(os.path.join(B, "events", vid + ".json")))
stt = json.load(open(os.path.join(B, "stt2", vid + ".json")))
words = [(w[0], w[1], w[2]) for s in stt["segments"] for w in (s.get("words") or [])]
cands = [e for e in ev["events"] if e["kind"] in ("add", "big") and e["start"] > 1.0]
if len(cands) > N:
    step = len(cands) / N
    cands = [cands[int(i * step)] for i in range(N)]
TW, TH, TXT = 640, 360, 92
font = ImageFont.truetype(os.path.join(FONTS, "Hind-SemiBold.ttf"), 22, layout_engine=ImageFont.Layout.RAQM)
fbold = ImageFont.truetype(os.path.join(FONTS, "Hind-Bold.ttf"), 24, layout_engine=ImageFont.Layout.RAQM)


def said(t):
    win = [w for w in words if t - 3.0 <= w[0] <= t + 1.5]
    if not win:
        return "", None
    near = min(win, key=lambda w: abs(w[0] - t))
    return " ".join(f"[{w[2]}]" if w is near else w[2] for w in win), near


def wrap(dr, text, width):
    lines, cur = [], ""
    for tok in text.split():
        trial = (cur + " " + tok).strip()
        if dr.textlength(trial, font=font) > width and cur:
            lines.append(cur)
            cur = tok
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines[:3]


out = os.path.join(B, "talmel", vid)
os.makedirs(out, exist_ok=True)
tiles, meta = [], []
with tempfile.TemporaryDirectory() as tmp:
    for i, e in enumerate(cands):
        t = round(e["end"] + 0.4, 2)
        p = os.path.join(tmp, f"{i:03d}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", f, "-frames:v", "1", "-vf", f"scale={TW}:{TH}", "-q:v", "3", p],
                       stdin=subprocess.DEVNULL)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        dr = ImageDraw.Draw(im)
        x0, y0, x1, y1 = e["bbox_frac"]
        top, band = 0.075 * TH, (0.93 - 0.075) * TH        # events.py measured inside the band without the channel bars
        dr.rectangle([x0 * TW - 4, top + y0 * band - 4, x1 * TW + 4, top + y1 * band + 4], outline=(230, 30, 40), width=4)
        text, near = said(e["start"])
        tile = Image.new("RGB", (TW, TH + TXT), (20, 20, 24))
        tile.paste(im, (0, 0))
        d2 = ImageDraw.Draw(tile)
        d2.text((8, TH + 2), f"#{i + 1}  {int(e['start'] // 60)}:{e['start'] % 60:04.1f}", fill=(255, 220, 60), font=fbold)
        for k, line in enumerate(wrap(d2, text, TW - 130)):
            d2.text((120, TH + 4 + k * 28), line, fill=(240, 240, 240), font=font)
        tiles.append(tile)
        meta.append({"tile": i + 1, "t_change": e["start"], "kind": e["kind"], "bbox_frac": e["bbox_frac"], "said": text,
                     "nearest_word": near[2] if near else None, "nearest_word_t": near[0] if near else None})
per, cols = 12, 3
for si in range(0, len(tiles), per):
    chunk = tiles[si:si + per]
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TW + (cols - 1) * 6, rows * (TH + TXT + 6)), "black")
    for k, tile in enumerate(chunk):
        sheet.paste(tile, ((k % cols) * (TW + 6), (k // cols) * (TH + TXT + 6)))
    sheet.save(os.path.join(out, f"sheet-{si // per + 1:02d}.jpg"), quality=82)
json.dump({"id": vid, "tiles": meta}, open(os.path.join(out, "tiles.json"), "w"), ensure_ascii=False, indent=0)
print(vid, "tiles", len(tiles), flush=True)
