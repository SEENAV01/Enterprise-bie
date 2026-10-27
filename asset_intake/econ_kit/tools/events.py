"""Visual change events of a build-up (canvas) video: when something new appears, how big, where.

Decodes at 5 fps, 192 px wide, grey, cropping the channel's top and bottom bars; a frame "changes" when more than
0.15% of pixels move by more than 24 levels from the previous frame; consecutive changing frames form one event.
Usage: events.py OUT.json VIDEO
"""
import json, subprocess, sys
import numpy as np
out, f = sys.argv[1], sys.argv[2]
W, FPS = 192, 5
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of",
                        "csv=p=0", f], capture_output=True, text=True).stdout.strip().split(",")
H = int(round(int(probe[1]) * W / int(probe[0]) / 2) * 2)
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f, "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt",
                      "gray", "-"], stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)
top, bot = int(H * 0.075), int(H * 0.93)
prev, rows, i = None, [], 0
while True:
    buf = p.stdout.read(W * H)
    if len(buf) < W * H:
        break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W)[top:bot].astype(np.int16)
    if prev is not None:
        m = np.abs(fr - prev) > 24
        frac = float(m.mean())
        if frac > 0.0015:
            ys, xs = np.nonzero(m)
            rows.append((i / FPS, frac, [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]))
        else:
            rows.append((i / FPS, 0.0, None))
    prev = fr
    i += 1
dur = i / FPS
events, cur = [], None
for t, frac, bb in rows:
    if frac > 0:
        if cur and t - cur["end"] <= 0.41:
            cur["end"] = t; cur["peak"] = max(cur["peak"], frac); cur["sum"] += frac
            cur["bbox"] = [min(cur["bbox"][0], bb[0]), min(cur["bbox"][1], bb[1]), max(cur["bbox"][2], bb[2]), max(cur["bbox"][3], bb[3])]
        else:
            cur = {"start": round(t - 1 / FPS, 2), "end": t, "peak": frac, "sum": frac, "bbox": bb}
            events.append(cur)
for e in events:
    e["end"] = round(e["end"], 2); e["peak"] = round(e["peak"], 4); e["sum"] = round(e["sum"], 4)
    x0, y0, x1, y1 = e["bbox"]; hh = bot - top
    e["bbox_frac"] = [round(x0 / W, 3), round(y0 / hh, 3), round(x1 / W, 3), round(y1 / hh, 3)]
    e["kind"] = "reset" if e["peak"] > 0.25 else ("big" if e["peak"] > 0.04 else "add")
json.dump({"video": f, "duration": round(dur, 1), "fps": FPS, "events": events}, open(out, "w"), indent=0)
gaps = np.diff([e["start"] for e in events]) if len(events) > 1 else np.array([0])
print(f.split("/")[-1], "dur", round(dur), "events", len(events), "resets", sum(e["kind"] == "reset" for e in events),
      "median gap", round(float(np.median(gaps)), 2))
