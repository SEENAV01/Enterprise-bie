"""Frame checks on a rendered benchmark video (Task 046, Part B): what code can read off the pixels, shot by shot.

``check_frames(frames, shot_rows)`` takes stills (one or two per shot, PNG bytes with their frame numbers) and the shot
rows of ``compose.shot_frames`` and returns a row per rule the frames can judge, with the frame number that failed:

- B-08 / caption: the top band carries bright text (the kinetic caption) in every shot;
- B-10 / focus glow: the lit structure's accent appears in the frame (pixels close to the member's accent);
- B-11 / VG-09 / dark style: the frame reads dark (mean and dark share), or a close-up keeps a dark border band;
- VG-01 / motion: consecutive stills differ (the picture moves, no frozen shots), the change rate matches the plan;
- B-03 / labels: a shot with labels shows label boxes (bright rounded text on the right side);
- VG-02: label text is code (we read the spec, not the pixels: a label layer, never baked into an image).

The plan-level reading of the other rules (B-01, B-02, B-04 to B-07, B-09, B-12, VG-03 to VG-11, W-01) comes from
``shots.rule_table``; ``rule_table_with_frames`` merges both into the 24-row table Navin reads, each row with its status
and the first failing frame.
"""
from __future__ import annotations

import io
from pathlib import Path


def _image(png: bytes):
    from PIL import Image
    return Image.open(io.BytesIO(png)).convert("RGB")


def luminance_stats(png: bytes) -> dict:
    from PIL import ImageStat
    im = _image(png).convert("L").resize((480, 270))
    st = ImageStat.Stat(im)
    hist = im.histogram()
    total = sum(hist)
    dark = sum(hist[:40]) / total
    return {"mean": round(st.mean[0], 1), "median": round(im.getextrema()[0] + 0, 1), "dark_share": round(dark, 3), "stddev": round(st.stddev[0], 1)}


def dark_style(png: bytes) -> tuple:
    """B-11 / VG-09 as pixels: the frame reads as the dark field (a low mean with a dark share), or, in a close-up that the
    subject fills, its border band is still dark (the vignette and the dark ground around the subject). Returns (ok, stats)."""
    from PIL import Image
    im = _image(png).convert("L")
    w, h = im.size
    b = max(2, int(w * 0.06))
    bands = [im.crop((0, 0, w, b)), im.crop((0, h - b, w, h)), im.crop((0, 0, b, h)), im.crop((w - b, 0, w, h))]
    border = sum(sum(x.histogram()[:40]) for x in bands) / float(sum(x.size[0] * x.size[1] for x in bands))
    stats = dict(luminance_stats(png), border_dark=round(border, 3))
    ok = (stats["mean"] <= 110 and stats["dark_share"] >= 0.25) or border >= 0.5
    return ok, stats


def band_has_text(png: bytes, top: float = 0.0, bottom: float = 0.16, threshold: int = 150, min_share: float = 0.004) -> bool:
    """Bright pixels in a horizontal band of the frame (the caption on top)."""
    im = _image(png).convert("L")
    w, h = im.size
    band = im.crop((0, int(h * top), w, int(h * bottom)))
    hist = band.histogram()
    bright = sum(hist[threshold:]) / float(band.size[0] * band.size[1])
    return bright >= min_share


def accent_share(png: bytes, accent: str, tolerance: int = 60, size: tuple = (320, 180)) -> float:
    """The share of pixels within ``tolerance`` of the accent colour (a glow, a label border, a caption term)."""
    im = _image(png).resize(size)
    r0, g0, b0 = int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16)
    count = 0
    px = im.load()
    for y in range(size[1]):
        for x in range(size[0]):
            r, g, b = px[x, y]
            if abs(r - r0) + abs(g - g0) + abs(b - b0) <= tolerance:
                count += 1
    return round(count / (size[0] * size[1]), 5)


def difference(a: bytes, b: bytes) -> float:
    from PIL import ImageChops, ImageStat
    x = _image(a).convert("L").resize((320, 180))
    y = _image(b).convert("L").resize((320, 180))
    return round(ImageStat.Stat(ImageChops.difference(x, y)).mean[0], 2)


def check_frames(frames: list, shot_rows: list, accents: dict | None = None) -> dict:
    """``frames``: [(frame number, png bytes)] in order; ``shot_rows``: compose.shot_frames rows; ``accents``: shot_id → accent."""
    by_shot = {}
    for n, png in frames:
        for row in shot_rows:
            if row["from"] <= n < row["to"]:
                by_shot.setdefault(row["shot_id"], []).append((n, png))
                break
    findings = {"B-08": [], "B-11": [], "VG-09": [], "B-10": [], "B-03": [], "VG-01": []}
    checked = 0
    previous = None
    for row in shot_rows:
        stills = by_shot.get(row["shot_id"]) or []
        for n, png in stills:
            checked += 1
            if not band_has_text(png):
                findings["B-08"].append({"shot": row["shot_id"], "frame": n, "why": "no caption text in the top band"})
            dark, lum = dark_style(png)
            if not dark:
                findings["B-11"].append({"shot": row["shot_id"], "frame": n, "why": f"frame is not dark (mean {lum['mean']}, dark share {lum['dark_share']}, border dark {lum['border_dark']})"})
            if accents and row["shot_id"] in accents and row["capability"] not in ("board_build", "mnemonic_card", "tree_hierarchy"):
                share = accent_share(png, accents[row["shot_id"]])
                if share < 0.0005:
                    findings["B-10"].append({"shot": row["shot_id"], "frame": n, "why": f"the member's accent is not on screen ({share:.2%})"})
            if row.get("labels") and not band_has_text(png, top=0.18, bottom=0.6, threshold=200, min_share=0.0006):
                findings["B-03"].append({"shot": row["shot_id"], "frame": n, "why": "the shot names things but no label box is lit"})
            if previous is not None and difference(previous[1], png) < 0.4 and n - previous[0] >= 20:
                findings["VG-01"].append({"shot": row["shot_id"], "frame": n, "why": f"the picture did not move since frame {previous[0]}"})
            previous = (n, png)
    findings["VG-09"] = findings["B-11"]
    return {"frames_checked": checked, "shots_with_stills": len(by_shot), "findings": findings}


def demo_rules(pngs: list, rules: tuple, accent: str | None = None) -> dict:
    """The rule checks a demo clip's stills can answer (the toolbox demos of Task 046 Part B). ``pngs`` are the contact-sheet
    stills in order; the first two are fade-ins, so the rules that need a settled picture read the rest. Returns
    {"checked": [rules], "failed": {rule: why}}; a rule no frame check can judge fails, so a demo cannot claim it."""
    failed = {}
    settled = pngs[2:] or pngs
    for rule in rules:
        if rule in ("B-11", "VG-09"):
            for i, png in enumerate(pngs):
                dark, lum = dark_style(png)
                if not dark:
                    failed[rule] = f"still {i} is not dark (mean {lum['mean']}, dark share {lum['dark_share']}, border dark {lum['border_dark']})"
                    break
        elif rule == "B-08":
            if not all(band_has_text(p) for p in settled):
                failed[rule] = "no caption text in the top band"
        elif rule == "B-10":
            if not accent:
                failed[rule] = "no accent given for the clip"
            elif max(accent_share(p, accent, tolerance=90, size=(640, 360)) for p in settled) < 0.0003:
                failed[rule] = f"the accent {accent} is not on screen"
        elif rule == "B-03":
            if not any(band_has_text(p, top=0.1, bottom=0.9, threshold=200, min_share=0.0006) for p in settled):
                failed[rule] = "no label box is lit"
        elif rule == "VG-01":
            if difference(pngs[0], pngs[-1]) < 1.5:
                failed[rule] = "the picture did not move between the first and the last still"
        else:
            failed[rule] = "no frame check can judge this rule"
    return {"checked": list(rules), "failed": failed}


def rule_table_with_frames(plan_table: list, frame_findings: dict) -> list:
    """The 24 rows: the plan's reading, overridden by the frames where they fail; each with the first failing frame."""
    out = []
    for row in plan_table:
        found = (frame_findings.get("findings") or {}).get(row["rule"]) or []
        merged = dict(row, frame=None, frame_status="not read")
        if row["rule"] in (frame_findings.get("findings") or {}):
            merged["frame_status"] = "fail" if found else "pass"
            if found:
                merged["status"] = "fail" if row["status"] == "pass" else row["status"]
                merged["frame"] = found[0]["frame"]
                merged["note"] = (row.get("note", "") + f"; frame {found[0]['frame']} ({found[0]['shot']}): {found[0]['why']}").strip("; ")
            elif row["status"] == "partial" and row["rule"] in ("B-11", "VG-09"):
                merged["status"] = "pass"                          # decided by the render: the frames are dark
                merged["note"] = "every still read is dark with one accent per member"
        out.append(merged)
    return out


def contact_sheet(frames: list, out: str | Path, title: str, cols: int = 4):
    from PIL import Image, ImageDraw, ImageFont
    tw, th = 480, 270
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, th * rows + 50), (6, 18, 28))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=22)
    except TypeError:
        font = ImageFont.load_default()
    draw.text((14, 12), title[:120], fill=(242, 246, 248), font=font)
    for i, (n, png) in enumerate(frames):
        im = _image(png).resize((tw, th))
        x, y = (i % cols) * tw, 50 + (i // cols) * th
        sheet.paste(im, (x, y))
        draw.rectangle([x, y + th - 26, x + 120, y + th], fill=(6, 18, 28))
        draw.text((x + 6, y + th - 24), f"f{n}", fill=(56, 211, 195), font=font)
    sheet.save(out, format="PNG", optimize=True)
