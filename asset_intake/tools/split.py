"""Split a video into shots: soft scene changes (ffmpeg scene score) plus a 15 s ceiling.

Usage: python3 split.py OUTDIR ID VIDEO LIMIT_S
Writes OUTDIR/ID/shots.json and numbered contact sheets OUTDIR/ID/sheet-NN.jpg (24 tiles each).
"""
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw

out, vid, f, limit = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
cap = float(sys.argv[5]) if len(sys.argv) > 5 else 15.0
d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                         capture_output=True, text=True).stdout)
end = min(d, limit)
r = subprocess.run(["ffmpeg", "-v", "info", "-t", f"{end:.2f}", "-i", f, "-an", "-vf",
                    "fps=10,scale=256:-2,select='gt(scene,0.14)',showinfo", "-f", "null", "-"],
                   capture_output=True, text=True, stdin=subprocess.DEVNULL)
cuts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
# merge cuts closer than 1.2 s (flashes, fast wipes)
bounds = [0.0]
for c in cuts:
    if c - bounds[-1] >= 1.2 and end - c >= 1.0:
        bounds.append(c)
bounds.append(end)
shots = []
for a, b in zip(bounds, bounds[1:]):
    n = max(1, int((b - a) // cap) + (1 if (b - a) % cap > 0.5 else 0))
    step = (b - a) / n
    for k in range(n):
        s, e = a + k * step, a + (k + 1) * step
        shots.append({"n": len(shots) + 1, "start": round(s, 2), "end": round(e, 2),
                      "kind": "cut" if k == 0 else "split"})
os.makedirs(os.path.join(out, vid), exist_ok=True)
portrait = None
tiles = []
with tempfile.TemporaryDirectory() as tmp:
    for sh in shots:
        t = (sh["start"] + sh["end"]) / 2
        p = os.path.join(tmp, f"{sh['n']:04d}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", f, "-frames:v", "1",
                        "-vf", "scale=400:-2", "-q:v", "4", p], stdin=subprocess.DEVNULL)
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            portrait = im.height > im.width
            if portrait:
                im = im.resize((200, int(im.height * 200 / im.width)))
            tiles.append((sh, im))
    per = 24
    for si in range(0, len(tiles), per):
        chunk = tiles[si:si + per]
        tw = max(im.width for _, im in chunk); th = max(im.height for _, im in chunk)
        cols = 6 if not portrait else 8
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * (th + 16)), "black")
        dr = ImageDraw.Draw(sheet)
        for k, (sh, im) in enumerate(chunk):
            x, y = (k % cols) * tw, (k // cols) * (th + 16)
            sheet.paste(im, (x, y + 16))
            fmt = lambda v: f"{int(v // 60)}:{int(v % 60):02d}"
            dr.text((x + 3, y + 2), f"#{sh['n']} {fmt(sh['start'])}-{fmt(sh['end'])}", fill="yellow")
        sheet.save(os.path.join(out, vid, f"sheet-{si // per + 1:02d}.jpg"), quality=78)
json.dump({"id": vid, "file": os.path.basename(f), "duration_s": round(d), "analysed_s": round(end),
           "cuts_found": len(cuts), "shots": shots}, open(os.path.join(out, vid, "shots.json"), "w"), indent=1)
print(vid, "shots", len(shots), "cuts", len(cuts), "sheets", (len(tiles) + 23) // 24)
