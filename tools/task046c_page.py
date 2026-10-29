"""The review page of a Task 046 Part C video for Navin: one HTML file from BIE's own run folders. No AI call, nothing written by hand.

    python -B tools/task046c_page.py --canvas <run folder with canvas.json, plans/, video_specs/> --render <folder with summary.json, cost.json>
        --html <page.html> [--video <review-720p.mp4>] [--stills <folder>] [--base-url https://raw.githubusercontent.com/.../runs/t046c-money-v1c]
        [--status "IMPLEMENTED ..."] [--note "..."]

The page carries the link to the ≤ 720p review copy, what BIE made (parts, modes B/C, levels, first-try passes, rounds, planned
seconds, the maker route and its cost), the render cost (render seconds per second of video, machine minutes, rupees at the list
price), one table row per part with its place, story flag, elements and longest still, one still per scene taken from the review
copy at the scene's middle (ffmpeg) or read from --stills, each part's spoken lines from the plans, the icon credits and the
questions for Navin. Short Hinglish for Navin; status words as they are.
"""
from __future__ import annotations

import argparse
import base64
import html
import io
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

MODE_WORDS = {"B": "B · build-up canvas + L3 touches", "C": "C · L3 world"}


def _jpeg_uri(data: bytes, width: int = 640, quality: int = 78) -> str:
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)))
    out = io.BytesIO()
    im.save(out, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def _rows(cells: list, head: bool = False) -> str:
    tag = "th" if head else "td"
    return "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"


def _mmss(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    return f"{seconds // 60}:{seconds % 60:02d}"


def scene_times(spec: dict) -> list:
    """[{id, start_s, seconds, mid_s}] from the spec's scene durations (frames at spec fps)."""
    fps = float(spec.get("fps") or 30)
    rows, at = [], 0
    for scene in spec.get("scenes", []):
        frames = int(scene.get("duration") or 0)
        rows.append({"id": scene.get("id", ""), "start_s": round(at / fps, 2), "seconds": round(frames / fps, 2),
                     "mid_s": round((at + frames / 2) / fps, 2), "frames": frames})
        at += frames
    return rows


def still_from_video(video: Path, at_s: float, out: Path) -> bool:
    """One JPEG from the review copy at at_s seconds, with ffmpeg; False when ffmpeg is missing or fails."""
    if not shutil.which("ffmpeg"):
        return False
    run = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at_s:.2f}", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(out)],
                         capture_output=True, text=True, timeout=120)
    return run.returncode == 0 and out.exists()


def collect_stills(times: list, *, video: Path | None, stills: Path | None, work: Path) -> dict:
    """Scene id → image bytes: --stills <folder>/<scene id>.(jpg|png) first, else a frame from the review copy at the scene's middle."""
    found = {}
    for row in times:
        if stills:
            for ext in ("jpg", "jpeg", "png"):
                p = stills / f"{row['id']}.{ext}"
                if p.exists():
                    found[row["id"]] = p.read_bytes()
                    break
        if row["id"] not in found and video and video.exists():
            out = work / f"{row['id']}.jpg"
            if still_from_video(video, row["mid_s"], out):
                found[row["id"]] = out.read_bytes()
    return found


def load_plans(canvas_dir: Path) -> dict:
    plans = {}
    for p in sorted((canvas_dir / "plans").glob("*.plan.json")) if (canvas_dir / "plans").exists() else []:
        plan = json.loads(p.read_text(encoding="utf-8"))
        plans[plan.get("id") or p.name.split(".")[0]] = plan
    return plans


def part_rows(video: dict, times: dict, plans: dict) -> str:
    e = html.escape
    out = []
    for p in video.get("parts", []):
        t = times.get(p["id"]) or {}
        problems = "; ".join(p.get("last_problems") or []) or ("; ".join(p.get("advisories") or []) if p.get("advisories") else "")
        out.append(_rows([f"<b>{e(p['id'])}</b>", e(p.get("part_id", "")), str(p.get("beats", len((plans.get(p["id"]) or {}).get("beats", [])))),
                          e(MODE_WORDS.get(p.get("mode", ""), p.get("mode", ""))), e(str(p.get("level", ""))),
                          e(p.get("place") or "—") + (" · story" if p.get("story") else ""),
                          ("✅ " if p.get("status") == "passed" else "❌ ") + e(str(p.get("status", ""))),
                          f"{p.get('rounds', '')}" + (" · first try" if p.get("first_try") else ""),
                          f"{_mmss(t.get('start_s', 0))} · {p.get('seconds', t.get('seconds', ''))} s" if t else f"{p.get('seconds', '')} s",
                          str(p.get("elements", "")), f"{p.get('longest_still_s', '')} s", e(problems)]))
    return "".join(out)


def script_block(video: dict, plans: dict) -> str:
    e = html.escape
    parts = []
    for p in video.get("parts", []):
        beats = (plans.get(p["id"]) or {}).get("beats") or []
        if not beats:
            continue
        lines = "".join(f"<li><span class='muted'>{e(str(b.get('beat_id', '')))}</span> {e(str(b.get('say', '')))}</li>" for b in beats)
        parts.append(f"<h4>{e(p['id'])} · {e(p.get('part_id', ''))} · {e(MODE_WORDS.get(p.get('mode', ''), p.get('mode', '')))}"
                     f"{' · ' + e(p['place']) if p.get('place') else ''}{' · story' if p.get('story') else ''}</h4><ol class='beats'>{lines}</ol>")
    return "".join(parts)


def plan_texts(canvas_dir: Path) -> dict:
    """{(plan id, text row id): text} over the plans of a canvas run, through the screen-text rows of each plan."""
    from bie.brain.video import screen_text
    out = {}
    for pid, plan in load_plans(canvas_dir).items():
        rows = screen_text.world_texts(plan) if "world_width" in plan or plan.get("kit") else screen_text.canvas_texts(plan)
        for r in rows:
            out[(pid, r["id"])] = r["text"]
    return out


def lesson_beats(lesson_dir: Path | None, video_id: str) -> dict:
    """{beat id: say} of one video of a lesson run, or {}."""
    if not lesson_dir or not (lesson_dir / "lesson_plan.json").exists():
        return {}
    plan = json.loads((lesson_dir / "lesson_plan.json").read_text(encoding="utf-8"))
    video = next((v for v in plan.get("videos") or [] if v.get("video_id") == video_id), None)
    return {b["beat_id"]: b.get("say", "") for b in (video or {}).get("beats") or []}


def before_after(video_id: str, canvas_dir: Path, before_canvas: Path | None, lesson_dir: Path | None, before_lesson: Path | None) -> str:
    """The before/after of Navin's verdict, by code: every on-screen text that changed between two canvas runs (by plan and
    element id) and every beat whose narration changed between two lesson runs."""
    e = html.escape
    parts = []
    if before_canvas and before_canvas.exists():
        old, new = plan_texts(before_canvas), plan_texts(canvas_dir)
        changed = [(k, old[k], new[k]) for k in sorted(old) if k in new and old[k] != new[k]]
        gone = [k for k in old if k not in new]
        added = [k for k in new if k not in old]
        parts.append(f"<h3>Screen par text: {len(changed)} badle, {len(gone)} hate, {len(added)} naye (plans by id)</h3>")
        if changed:
            parts.append('<div class="scroll"><table>' + _rows(["part · element", "pehle", "ab"], head=True)
                         + "".join(_rows([e(f"{k[0]} · {k[1]}"), e(o).replace("\n", "<br>"), e(n).replace("\n", "<br>")]) for k, o, n in changed) + "</table></div>")
        if gone or added:
            parts.append('<details><summary>Hate aur naye texts</summary><div class="scroll"><table>' + _rows(["kya", "part · element", "text"], head=True)
                         + "".join(_rows(["hata", e(f"{k[0]} · {k[1]}"), e(old[k]).replace("\n", "<br>")]) for k in gone)
                         + "".join(_rows(["naya", e(f"{k[0]} · {k[1]}"), e(new[k]).replace("\n", "<br>")]) for k in added) + "</table></div></details>")
    if before_lesson and lesson_dir:
        old, new = lesson_beats(before_lesson, video_id), lesson_beats(lesson_dir, video_id)
        changed = [(b, old[b], new[b]) for b in old if b in new and old[b] != new[b]]
        parts.append(f"<h3>Narration: {len(changed)} of {len(old)} beats badle</h3>")
        if changed:
            parts.append('<div class="scroll"><table>' + _rows(["beat", "pehle", "ab"], head=True)
                         + "".join(_rows([e(b), e(o), e(n)]) for b, o, n in changed) + "</table></div>")
    return "".join(parts)


def build(canvas_dir: Path, render_dir: Path, *, video_path: Path | None = None, stills_dir: Path | None = None, base_url: str = "",
          status: str = "", note: str = "", before_canvas: Path | None = None, lesson_dir: Path | None = None,
          before_lesson: Path | None = None) -> str:
    e = html.escape
    canvas = json.loads((canvas_dir / "canvas.json").read_text(encoding="utf-8"))
    quality = canvas.get("quality") or {}
    render = json.loads((render_dir / "summary.json").read_text(encoding="utf-8")) if (render_dir / "summary.json").exists() else {}
    cost = render.get("cost") or (json.loads((render_dir / "cost.json").read_text(encoding="utf-8")) if (render_dir / "cost.json").exists() else {})
    join = render.get("join") or {}
    run_summary = json.loads((canvas_dir / "SUMMARY.json").read_text(encoding="utf-8")) if (canvas_dir / "SUMMARY.json").exists() else {}
    subscription = ((run_summary.get("cost") or {}).get("subscription")) or {}
    spent_inr = ((run_summary.get("cost") or {}).get("total_inr"))
    plans = load_plans(canvas_dir)
    videos = canvas.get("videos") or []
    course = canvas.get("course") or {}
    review_name = Path(join.get("review") or "review-720p.mp4").name
    video_url = f"{base_url}/{review_name}" if base_url else ""
    status = status or "IMPLEMENTED aur INTEGRATED (plans BIE ne likhe, render BIE ke code ne CI mein kiya); ACCEPTED nahi, Navin ke verdict tak"
    head = f"""<title>{e(course.get('title') or 'BIE video')} · review</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root {{ --bg:#f6f4ee; --fg:#1d2328; --muted:#5f6b72; --card:#ffffff; --line:#d9d4c7; --accent:#8a5a14; --accent-ink:#fff8ea; --green:#1d7a4f; --warm:#b85c00; color-scheme:light }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#141a1f; --fg:#f1efe8; --muted:#a3adb3; --card:#1d262d; --line:#324049; --accent:#e4b263; --accent-ink:#141a1f; --green:#5ad395; --warm:#ffb35c; color-scheme:dark }} }}
:root[data-theme="dark"] {{ --bg:#141a1f; --fg:#f1efe8; --muted:#a3adb3; --card:#1d262d; --line:#324049; --accent:#e4b263; --accent-ink:#141a1f; --green:#5ad395; --warm:#ffb35c; color-scheme:dark }}
body {{ background:var(--bg); color:var(--fg); font-family: Inter, "Noto Sans", "Noto Sans Devanagari", system-ui, sans-serif; line-height:1.5; margin:0;
  padding-block:24px 48px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)) }}
main {{ max-width: 1100px; margin: 0 auto }}
h1 {{ font-size: clamp(24px, 4vw, 36px); margin: 0 0 6px; text-wrap: balance }}
h2 {{ font-size: clamp(20px, 3vw, 26px); margin: 36px 0 10px; color: var(--accent); text-wrap: balance }}
h3 {{ font-size: 17px; margin: 18px 0 8px }}
h4 {{ font-size: 15px; margin: 16px 0 6px }}
p.lead {{ font-size: 17px }}
.muted {{ color: var(--muted) }}
.tag {{ display:inline-block; padding:2px 10px; border:1px solid var(--line); border-radius:999px; font-size:12px; letter-spacing:.04em; text-transform:uppercase; color:var(--muted) }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px }}
.card {{ background: var(--card); border:1px solid var(--line); border-radius: 14px; padding: 14px 16px; min-width: 0 }}
.card h3 {{ margin-top: 0 }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px }}
td, th {{ text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--line); vertical-align: top }}
th {{ color: var(--muted); font-weight: 600; font-size: 12px; letter-spacing: .04em; text-transform: uppercase }}
.scroll {{ overflow-x: auto; border:1px solid var(--line); border-radius: 12px; background: var(--card) }}
a.button {{ display:inline-block; background: var(--accent); color: var(--accent-ink); font-weight: 700; padding: 10px 18px; border-radius: 10px; text-decoration: none }}
.stills {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px }}
figure {{ margin: 0; min-width: 0 }}
figure img {{ display:block; width: 100%; max-width: 100%; height: auto; border-radius: 10px; border: 1px solid var(--line) }}
figcaption {{ font-size: 13px; color: var(--muted); margin-top: 4px }}
details summary {{ cursor: pointer; font-weight: 600; margin: 12px 0 }}
ol.beats {{ padding-left: 20px; font-size: 15px }}
ol.beats li {{ margin: 4px 0 }}
ul {{ padding-left: 20px }}
.decide {{ border-left: 4px solid var(--warm); padding: 6px 14px; background: var(--card); border-radius: 0 12px 12px 0 }}
</style>"""
    parts = [head, "<main>", f'<span class="tag">Task 046 · Part C · {e(status)}</span>']
    for video in videos:
        spec_path = canvas_dir / "video_specs" / f"{video['video_id']}.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8")) if spec_path.exists() else {"scenes": []}
        times = {t["id"]: t for t in scene_times(spec)}
        parts.append(f"<h1>{e(video['video_id'])} · {e(video.get('title', ''))}</h1>")
        parts.append(f'<p class="lead">{e(course.get("title", ""))} · {e(course.get("subject", ""))} · {e(course.get("learners", ""))}. '
                     f'{len(video.get("parts", []))} parts, {video.get("seconds")} s planned'
                     + (f', {cost.get("video_minutes")} min rendered' if cost.get("video_minutes") else "")
                     + '. Awaaz nahi, captions hain (asli voice Task 047). '
                     + (e(note) if note else "") + "</p>")
        if video_url:
            parts.append(f'<p class="lead"><a class="button" href="{e(video_url)}" target="_blank" rel="noopener">▶ Video dekho (review copy, '
                         f'{(join.get("review_bytes") or 0) / 1e6:.1f} MB, 720p)</a> <span class="muted">nayi tab mein khulega; full 1080p MP4 CI artifact mein hai.</span></p>')
        parts.append('<div class="grid">')
        parts.append('<div class="card"><h3>BIE ne kya banaya</h3><table>' +
                     _rows(["parts passed", f"{video.get('parts_passed')} of {len(video.get('parts', []))}"]) +
                     _rows(["first try", f"{video.get('first_try_passes')} of {len(video.get('parts', []))} ({quality.get('first_try_rate', 0):.0%})"]) +
                     _rows(["rounds (maker calls)", str(video.get("rounds"))]) +
                     _rows(["modes", f"B {video.get('modes', {}).get('B', 0)} · C {video.get('modes', {}).get('C', 0)}"]) +
                     _rows(["story parts in a world", f"{quality.get('story_parts_in_a_world', 0)} of {quality.get('story_parts', 0)}"]) +
                     _rows(["missing kits", e(", ".join(quality.get("missing_kits") or [])) or "none"]) +
                     _rows(["maker", e(str(canvas.get("maker_route", "")))]) +
                     _rows(["AI cost", (f"₹{spent_inr}" if spent_inr is not None else "₹0") +
                            (f" · ChatGPT plan {subscription.get('calls')} calls, {subscription.get('minutes')} min" if subscription else "")]) +
                     "</table></div>")
        if cost:
            parts.append('<div class="card"><h3>Render (GitHub runner, no GPU)</h3><table>' +
                         _rows(["video", f"{cost.get('video_minutes')} min · {cost.get('frames')} frames @ 30 fps, 1920 × 1080"]) +
                         _rows(["chunks in parallel", str(cost.get("chunks"))]) +
                         _rows(["wall clock", f"{cost.get('wall_clock_minutes_parallel')} min"]) +
                         _rows(["machine minutes", str(cost.get("machine_minutes"))]) +
                         _rows(["render seconds per video second", str(cost.get("seconds_per_video_second"))]) +
                         _rows(["list price", f"₹{cost.get('inr_at_list_price')} (billed ₹0: public repo)"]) +
                         _rows(["run", f'<a href="{e(str(render.get("run_url", "")))}" target="_blank" rel="noopener">{e(str(render.get("run_id", "")))}</a> from {e(str(render.get("sha", ""))[:8])}' if render.get("run_id") else "—"]) +
                         "</table></div>")
        parts.append('<div class="card"><h3>Kisne kya kiya</h3><ul>'
                     '<li>Script: BIE ka lesson section (Section 2), Codex maker, code checks + Codex reviewer.</li>'
                     '<li>Plans (canvas B / world C): BIE ka director, Codex maker, code checks; har part ka plan <code>plans/</code> mein.</li>'
                     '<li>Render: BIE ka code, GitHub Actions mein, chunks parallel.</li>'
                     '<li>Claude ne koi script, plan, scene ya frame haath se nahi likha; ye page bhi <code>tools/task046c_page.py</code> ne banaya.</li>'
                     '</ul></div>')
        parts.append("</div>")
        parts.append("<h2>Parts</h2>")
        parts.append('<div class="scroll"><table>' + _rows(["part", "chapter part", "beats", "mode", "level", "place", "status", "rounds", "video time · length", "elements", "longest still", "notes"], head=True)
                     + part_rows(video, times, plans) + "</table></div>")
        stills_work = Path(tempfile.mkdtemp(prefix="bie-page-"))
        found = collect_stills(list(times.values()), video=video_path, stills=stills_dir, work=stills_work)
        if found:
            parts.append("<h2>Ek still har scene se (review copy ke beech ka frame)</h2>")
            parts.append('<div class="stills">')
            by_id = {p["id"]: p for p in video.get("parts", [])}
            for t in times.values():
                if t["id"] not in found:
                    continue
                p = by_id.get(t["id"]) or {}
                cap = f"{t['id']} · {_mmss(t['mid_s'])}" + (f" · {MODE_WORDS.get(p.get('mode', ''), p.get('mode', ''))}" if p else "") + (f" · {p['place']}" if p.get("place") else "")
                parts.append(f'<figure><img alt="{e(t["id"])}" src="{_jpeg_uri(found[t["id"]])}"><figcaption>{e(cap)}</figcaption></figure>')
            parts.append("</div>")
        shutil.rmtree(stills_work, ignore_errors=True)
        script = script_block(video, plans)
        if script:
            parts.append(f"<details><summary>Script, part by part (jo captions mein dikhta hai)</summary>{script}</details>")
        if video.get("credits"):
            parts.append("<details><summary>Icon credits</summary><ul>" + "".join(f"<li>{e(c)}</li>" for c in video["credits"]) + "</ul></details>")
        if before_canvas or before_lesson:
            parts.append("<h2>Pehle aur ab (Navin ka verdict, 29 October 2026)</h2>")
            parts.append(before_after(video["video_id"], canvas_dir, before_canvas, lesson_dir, before_lesson))
    parts.append('<section id="decide"><h2>Navin ke faisle</h2><div class="decide"><ul>'
                 '<li><b>Verdict:</b> video dekh kar: kya ye economy chapter ke liye sahi disha hai? Kya sabse pehle sudhre?</li>'
                 '<li><b>B default, C story ke liye:</b> parts table mein har part ka mode hai; koi part galat mode mein lage to bolo.</li>'
                 '<li><b>Examples lock karna:</b> explanations.json mein koi example lock karna aapka faisla hai.</li>'
                 '</ul></div></section>')
    parts.append("</main>")
    return "\n".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--canvas", required=True, type=Path, help="run folder with canvas.json, plans/, video_specs/")
    parser.add_argument("--render", required=True, type=Path, help="published render folder with summary.json and cost.json")
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--video", type=Path, help="the review copy; one still per scene is taken from it")
    parser.add_argument("--stills", type=Path, help="folder with <scene id>.jpg|png stills (used before --video)")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--status", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--before-canvas", type=Path, help="an earlier canvas run: every on-screen text that changed is listed")
    parser.add_argument("--lesson", type=Path, help="the lesson run whose script this video follows (for the narration before/after)")
    parser.add_argument("--before-lesson", type=Path, help="an earlier lesson run: every beat whose narration changed is listed")
    args = parser.parse_args(argv)
    page = build(args.canvas, args.render, video_path=args.video, stills_dir=args.stills, base_url=args.base_url.rstrip("/"),
                 status=args.status, note=args.note, before_canvas=args.before_canvas, lesson_dir=args.lesson, before_lesson=args.before_lesson)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(page, encoding="utf-8")
    print(f"{args.html}: {len(page.encode('utf-8')) / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
