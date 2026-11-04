"""Readable keyframe sheets for a build-up canvas video (batch 3).

A frame every STEP seconds, taken just before the step ends (the canvas as built by then), plus the frame just before
each canvas reset (from events/<ID>.json), so every built canvas is seen once. Tiles are 640 px wide, 3 x 4 per sheet,
each tile labelled with its time. Usage: keyframes.py ID [STEP]
Writes kf/<ID>/sheet-NN.jpg and kf/<ID>/frames.json (sheet, tile, time).
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

B = os.path.dirname(os.path.abspath(__file__))
vid = sys.argv[1]
step = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
f = os.path.join(B, "vids", vid + ".mp4")
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                           capture_output=True, text=True).stdout)
ev = json.load(open(os.path.join(B, "events", vid + ".json")))["events"]
times = [min(dur - 0.2, k * step - 0.3) for k in range(1, int(dur // step) + 2) if k * step - 0.3 < dur + step]
resets = [e["start"] - 0.3 for e in ev if e["kind"] == "reset" and e["start"] > 2]
for r in resets:
    times = [t for t in times if abs(t - r) > 3.0]
times = sorted(set(round(t, 2) for t in times + resets if 0.5 < t < dur))
out = os.path.join(B, "kf", vid)
os.makedirs(out, exist_ok=True)
font = ImageFont.load_default()
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
except OSError:
    pass
tiles = []
with tempfile.TemporaryDirectory() as tmp:
    for i, t in enumerate(times):
        p = os.path.join(tmp, f"{i:04d}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", f, "-frames:v", "1", "-vf", "scale=640:-2",
                        "-q:v", "3", p], stdin=subprocess.DEVNULL)
        if os.path.exists(p):
            tiles.append((t, Image.open(p).convert("RGB")))
per, cols = 12, 3
meta = []
for si in range(0, len(tiles), per):
    chunk = tiles[si:si + per]
    tw, th = 640, max(im.height for _, im in chunk)
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols - 1) * 6, rows * (th + 30)), "black")
    dr = ImageDraw.Draw(sheet)
    for k, (t, im) in enumerate(chunk):
        x, y = (k % cols) * (tw + 6), (k // cols) * (th + 30)
        sheet.paste(im, (x, y + 30))
        dr.text((x + 6, y + 3), f"{int(t // 60)}:{t % 60:04.1f}", fill="yellow", font=font)
        meta.append({"sheet": si // per + 1, "tile": k + 1, "t": t})
    sheet.save(os.path.join(out, f"sheet-{si // per + 1:02d}.jpg"), quality=82)
json.dump({"id": vid, "duration": round(dur, 1), "step": step, "frames": meta}, open(os.path.join(out, "frames.json"), "w"))
print(vid, "frames", len(tiles), "sheets", (len(tiles) + per - 1) // per, flush=True)
