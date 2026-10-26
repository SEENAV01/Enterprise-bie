"""The review page of a benchmark render for Navin (Task 046, Part B): one HTML file from the published folder.

    python -B tools/benchmark_page.py --out <folder with summary.json, A/, C/, bridge/> --html <page.html>
        [--base-url https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/t046-v3-benchmark]

The page carries, per route, the link to the ≤ 720p review copy, the cost table (render seconds per second of video, machine
minutes, rupees at the list price), the level split and the pace, the 24-rule table with frame numbers, the shot list, the
contact sheets (one still per shot) and the bridge comparison (real Remotion against the preview path). Short Hinglish for
Navin; status words as they are (IMPLEMENTED until his verdict). No AI call.
"""
from __future__ import annotations

import argparse
import base64
import html
import io
import json
from pathlib import Path

STATUS_WORDS = {"pass": "✅ pass", "partial": "🟡 partial", "fail": "❌ fail", "n/a": "— n/a", "not read": "— not read"}


def _sheet_uri(path: Path, width: int = 960) -> str:
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im = im.resize((width, int(im.height * width / im.width)))
    out = io.BytesIO()
    im.save(out, format="JPEG", quality=80, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def _rows(cells: list, head: bool = False) -> str:
    tag = "th" if head else "td"
    return "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"


def route_section(route: str, report: dict, folder: Path, base_url: str) -> str:
    cost = report.get("cost") or {}
    e = html.escape
    video = f"{base_url}/{route}/{report['review']}" if base_url and report.get("review") else ""
    levels = ", ".join(f"{k} {v['seconds']} s ({v['share']:.0%})" for k, v in (report.get("level_seconds") or {}).items())
    pace = report.get("pace") or {}
    tally = report.get("tally") or {}
    parts = [f'<section id="route-{route}"><h2>Route {e(route)} · {"procedural three.js world" if route == "A" else "Blender-made glTF sheets in the same world"}</h2>']
    if video:
        parts.append(f'<p class="lead"><a class="button" href="{e(video)}" target="_blank" rel="noopener">▶ Video dekho (review copy, {(report.get("review_bytes") or 0) / 1e6:.1f} MB, 720p)</a> '
                     f'<span class="muted">nayi tab mein khulega; download bhi wahin se.</span></p>')
    parts.append('<div class="grid">')
    parts.append('<div class="card"><h3>Kitna render hua</h3><table>' +
                 _rows(["shots", str(report["shots"])]) + _rows(["seconds (credits ke saath)", str(report["seconds"])]) +
                 _rows(["spoken seconds", str(report.get("spoken_seconds"))]) + _rows(["frames", f"{report['frames']} @ 30 fps, 1920 × 1080"]) +
                 _rows(["voice", e(str(report.get("voice")))]) + _rows(["members dikhe", e(", ".join(report.get("members") or []))]) +
                 (_rows(["Blender models", e(", ".join(report.get("models") or []))]) if report.get("models") else "") + "</table></div>")
    parts.append('<div class="card"><h3>Level aur pace</h3><table>' +
                 _rows(["level split (seconds)", e(levels)]) + _rows(["main level", e(str(report.get("main_level")))]) +
                 _rows(["visual changes", str(pace.get("changes"))]) + _rows(["one change every", f"{pace.get('seconds_per_change')} s (target {pace.get('target_seconds')} s, band {e(str(pace.get('band')))})"]) +
                 "</table></div>")
    parts.append('<div class="card"><h3>Render cost (GitHub runner, 2 vCPU, no GPU)</h3><table>' +
                 _rows(["render seconds per second of video", str(cost.get("seconds_per_video_second"))]) + _rows(["machine minutes", str(cost.get("machine_minutes"))]) +
                 _rows(["wall clock (chunks in parallel)", f"{cost.get('wall_clock_minutes_parallel')} min"]) +
                 _rows(["list price", f"USD {cost.get('usd_at_list_price')} = ₹{cost.get('inr_at_list_price')} (₹0 billed: public repo)"]) +
                 _rows(["chunks", str(cost.get("chunks"))]) + "</table></div>")
    parts.append("</div>")
    parts.append(f'<h3>24-rule table (frame checks: {report.get("frames_checked")} stills, one per shot) · {e(str(tally))}</h3>')
    parts.append('<div class="scroll"><table class="rules">' + _rows(["rule", "status", "frame", "note"], head=True))
    for r in report.get("rule_table") or []:
        parts.append(_rows([e(r["rule"]), STATUS_WORDS.get(r["status"], e(r["status"])), e(str(r.get("frame") if r.get("frame") is not None else "")), e(str(r.get("note", "")))]))
    parts.append("</table></div>")
    sheets = [folder / name for name in report.get("contact_sheets") or [] if (folder / name).exists()]
    if sheets:
        parts.append("<h3>Contact sheets (har shot ki ek still)</h3>")
        for sheet in sheets:
            parts.append(f'<img class="sheet" alt="{e(sheet.name)}" src="{_sheet_uri(sheet)}">')
    shots_md = folder / "SHOTS.md"
    if shots_md.exists():
        rows = [l for l in shots_md.read_text(encoding="utf-8").splitlines() if l.startswith("| b")]
        parts.append(f'<details><summary>Shot list, shot by shot ({len(rows)} shots)</summary><div class="scroll"><table>' +
                     _rows(["shot", "frames", "s", "level", "capability", "camera", "labels", "sentence"], head=True))
        for line in rows:
            cells = [c.strip() for c in line.strip("|").split("|")]
            parts.append(_rows([e(c) for c in cells]))
        parts.append("</table></div></details>")
    parts.append("</section>")
    return "\n".join(parts)


def build(out: Path, base_url: str) -> str:
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    routes = summary.get("routes") or {}
    bridge = summary.get("bridge")
    e = html.escape
    first = next(iter(routes.values()), {})
    head = f"""<title>v3 Benchmark Render</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root {{ --bg:#f4f7f9; --fg:#10222c; --muted:#5b6b74; --card:#ffffff; --line:#d6dfe4; --accent:#0b7f73; --warm:#b85c00; --ink:#10222c; color-scheme:light }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#06121c; --fg:#f2f6f8; --muted:#9fb3bd; --card:#0d1f2b; --line:#1f3a48; --accent:#38d3c3; --warm:#ffb35c; --ink:#f2f6f8; color-scheme:dark }} }}
:root[data-theme="dark"] {{ --bg:#06121c; --fg:#f2f6f8; --muted:#9fb3bd; --card:#0d1f2b; --line:#1f3a48; --accent:#38d3c3; --warm:#ffb35c; --ink:#f2f6f8; color-scheme:dark }}
body {{ background:var(--bg); color:var(--fg); font-family: Inter, "Noto Sans", "Noto Sans Devanagari", system-ui, sans-serif; line-height:1.5; margin:0;
  padding-block:24px 48px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)) }}
main {{ max-width: 1100px; margin: 0 auto }}
h1 {{ font-size: clamp(26px, 4vw, 38px); margin: 0 0 6px; text-wrap: balance }}
h2 {{ font-size: clamp(20px, 3vw, 26px); margin: 36px 0 10px; color: var(--accent); text-wrap: balance }}
h3 {{ font-size: 17px; margin: 18px 0 8px }}
p.lead {{ font-size: 17px }}
.muted {{ color: var(--muted) }}
.tag {{ display:inline-block; padding:2px 10px; border:1px solid var(--line); border-radius:999px; font-size:13px; letter-spacing:.04em; text-transform:uppercase; color:var(--muted) }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px }}
.card {{ background: var(--card); border:1px solid var(--line); border-radius: 14px; padding: 14px 16px; min-width: 0 }}
.card h3 {{ margin-top: 0 }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px }}
td, th {{ text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--line); vertical-align: top }}
th {{ color: var(--muted); font-weight: 600; font-size: 12px; letter-spacing: .04em; text-transform: uppercase }}
.scroll {{ overflow-x: auto; border:1px solid var(--line); border-radius: 12px; background: var(--card) }}
.rules td:nth-child(4) {{ max-width: 640px }}
a.button {{ display:inline-block; background: var(--accent); color: #06121c; font-weight: 700; padding: 10px 18px; border-radius: 10px; text-decoration: none }}
img.sheet {{ display:block; width: 100%; max-width: 100%; height: auto; border-radius: 10px; border: 1px solid var(--line); margin: 8px 0 }}
details summary {{ cursor: pointer; font-weight: 600; margin: 12px 0 }}
ul {{ padding-left: 20px }}
.decide {{ border-left: 4px solid var(--warm); padding: 6px 14px; background: var(--card); border-radius: 0 12px 12px 0 }}
</style>"""
    parts = [head, "<main>", '<span class="tag">Task 046 · Part B · IMPLEMENTED (ACCEPTED nahi, Navin ke verdict tak)</span>',
             f'<h1>v3 ka epithelium family segment, BIE ke code se render</h1>',
             f'<p class="lead">Script: v3 (passed, W-01 patched). Segment: parts {e(", ".join(first.get("parts") or []))}, {first.get("shots")} shots, '
             f'{first.get("seconds")} s. Voice: placeholder (eSpeak NG) sirf timing ke liye; asli voice Task 047. Run {e(str(summary.get("run_id")))} from {e(str(summary.get("sha") or ""))[:8]}.</p>',
             '<p class="muted">Har route ki video ka link upar; neeche level split, pace, render cost, 24-rule table (frame number ke saath), contact sheets aur shot list.</p>']
    for route, report in routes.items():
        parts.append(route_section(route, report, out / route, base_url))
    if bridge:
        parts.append('<section id="bridge"><h2>Bridge · real Remotion vs preview path (route A ke pehle 10 s)</h2>')
        parts.append('<div class="card"><table>' + _rows(["Remotion render seconds per video second (bundling included)", str(bridge.get("seconds_per_video_second"))]) +
                     _rows(["preview path render seconds per video second", str((bridge.get("preview") or {}).get("seconds_per_video_second"))]) +
                     _rows(["frame difference (mean grey levels, < 8 passes)", e(str(bridge.get("mean_differences")))]) +
                     _rows(["verdict", "same picture" if bridge.get("passed") else "DIFFERENT"]) + "</table></div>")
        sheet = out / "bridge" / "bridge_sheet.png"
        if sheet.exists():
            parts.append(f'<img class="sheet" alt="bridge sheet" src="{_sheet_uri(sheet)}">')
        parts.append("</section>")
    parts.append('<section id="decide"><h2>Navin ke faisle</h2><div class="decide"><ul>'
                 '<li><b>Verdict:</b> video dekh kar: kya ye benchmark ki disha mein hai? Kaun si cheez sabse pehle sudhre (Part C)?</li>'
                 '<li><b>Render machine aur GPU budget:</b> ab 2-vCPU GitHub runner par, no GPU, ₹0 billed; cost table upar list price par hai.</li>'
                 '<li><b>Block approvals:</b> 18 blocks ke demo clips toolbox lane mein (batch 1, group bench); koi block hataana ya badalna ho to bolo.</li>'
                 '<li><b>Route:</b> A (procedural) ya C (Blender models) — dono ki cost aur picture upar.</li>'
                 '</ul></div></section>')
    parts.append("</main>")
    return "\n".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True)
    parser.add_argument("--html", required=True)
    parser.add_argument("--base-url", default="")
    args = parser.parse_args(argv)
    page = build(Path(args.out), args.base_url.rstrip("/"))
    Path(args.html).write_text(page, encoding="utf-8")
    print(f"{args.html}: {len(page.encode('utf-8')) / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
