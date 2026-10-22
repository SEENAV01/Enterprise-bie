"""Run BIE brain sections on a real chapter.

  --section understand   Section 1: the chapter PDF → chapter_map.json, MAP.md
  --section lesson       Section 2: a chapter map (--chapter-map, path or https URL) → lesson_plan.json, SCRIPT.md
  --section director     Section 3: --from-run (folder or URL with chapter_map.json and lesson_plan.json) → director.json
  --section notes        Section 7: --chapter-map → notes.json, NOTES.html (interactive slides; print view = PDF)
  --section game         Section 6 (design): --chapter-map → game_design.json, GAME.md
  --section visual       Section 4: --from-run (with director.json) → assets/, video_specs/, VISUAL.md, stills/; --render adds MP4 previews
  --section chain        Sections 1, 2, 3, 6 (design) and 7 in one run; --with-visual adds Section 4

  python tools/run_brain.py --section understand --source <pdf path or https URL> --out <dir> \
      --title "10. Tissues and Its Types" --subject "Science and Technology" --learners "UPSC / State PCS aspirants" \
      --exam "UPSC / State PCS" --language Hinglish --maker anthropic --reviewer openai

Keys come only from environment variables (GitHub Actions secrets). The maker and the reviewer must be
different providers; while only one provider key is usable, the same provider is allowed with another
model (--reviewer-model; temporary, marked "same_company_temporary" in every record). Outputs in --out:
chapter_map.json, MAP.md, records/ (one process record per step, images by hash only), LEDGER.jsonl (every
provider call with tokens and estimated cost) and SUMMARY.json (also printed as ::notice annotations).
--fake runs offline with the deterministic brain fake.

Cost guard ("pahra", bie/model_gateway/live/budget.py): before any work, an estimate in rupees per section
("Andaaza Rs X, seema Rs Y") and one tiny preflight call per route; a failed preflight (balance, budget,
key) stops the run before real work. --max-inr (default 300) is a hard cap checked before every call: a
call that would cross it is not sent, passed work is kept and the status is "stopped: budget". SUMMARY.json
reports rupees per section and per page (price-table estimates, not the bill) and keeps real_bill_inr for
the dashboard amount.

Codex maker (Task 044): --maker codex runs the maker through OpenAI's Codex CLI signed in with Navin's
ChatGPT Pro plan (``codex exec``; BIE_CODEX_BIN names the CLI, BIE_CODEX_MODEL the model). It runs only on
Navin's private machine (deployment/codex-vm/), never in this public repository's GitHub Actions. Its calls
cost no rupees; they use the plan, whose usage is shown before and after the run. A used-up plan window
ends the run as "stopped: plan limit"; --resume-from continues it later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import cost as cost_module  # noqa: E402
from bie.brain import rulebook as rulebook_module  # noqa: E402
from bie.brain.fake import BrainFakeClient  # noqa: E402
from bie.brain.pages import parse_page_range  # noqa: E402
from bie.brain.runner import SectionRunner  # noqa: E402
from bie.brain.director import run_director  # noqa: E402
from bie.brain.game import run_game_design  # noqa: E402
from bie.brain.lesson import run_lesson  # noqa: E402
from bie.brain.notes import run_notes  # noqa: E402
from bie.brain.understanding import Course, run_chapter  # noqa: E402
from bie.brain.visual import run_visual  # noqa: E402
from bie.model_gateway.gpt_adapter import GPTAdapter  # noqa: E402
from bie.model_gateway.live.budget import COST_NOTE, CostGuard, preflight, preflight_message, usd_inr  # noqa: E402
from bie.model_gateway.live.codex_client import DEFAULT_MODEL as CODEX_MODEL, CodexExecClient  # noqa: E402
from bie.model_gateway.live.pricing import SUBSCRIPTION_VIAS  # noqa: E402
from bie.model_gateway.live.config import (ADAPTERS, MODEL_ENV, PROVIDERS, VIA_ENV, all_keys, build_routes,  # noqa: E402
                                           make_client, route_for)
from bie.model_gateway.live.errors import redact  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402
from bie.model_gateway.live.ledger import UsageLedger  # noqa: E402
from run_blind_test import apply_overrides, notice, read_source  # noqa: E402


def read_text(source: str) -> str:
    if source.startswith("https://"):
        import urllib.request
        with urllib.request.urlopen(urllib.request.Request(source, headers={"user-agent": "bie-brain/1"}), timeout=120) as response:
            return response.read(50 * 1024 * 1024).decode("utf-8")
    path = (ROOT / source).resolve() if not Path(source).is_absolute() else Path(source)
    return path.read_text(encoding="utf-8")


def build_gateway(maker, reviewer, *, fake, ledger, max_output_tokens, reviewer_model="", guard=None):
    """(gateway, reviewer route). A same-provider reviewer gets its own route ``<provider>-checker`` with
    ``reviewer_model``, which must differ from the maker's model; ``reviewer_model="same"`` is the one explicit
    exception (the key allows a single model: the maker's model checks in a fresh call, marked
    same_model_temporary, kamzor jaanch). The ``codex`` maker always runs the Codex CLI named by BIE_CODEX_BIN
    (``--fake`` replaces only the API routes, so tests use a fake executable)."""
    same = maker == reviewer
    if same and not reviewer_model:
        raise SystemExit("MAKER_AND_REVIEWER_MUST_DIFFER: a same-company checker needs --reviewer-model")
    providers = [maker] if same else [p for p in (maker, reviewer) if p and p != "codex"]
    if fake:
        routes = {p: ADAPTERS[p](BrainFakeClient(p), f"fake-{p}") for p in providers}
    else:
        routes, missing = build_routes(providers, max_output_tokens=max_output_tokens, stream=True)
        if missing:
            raise SystemExit("NOT_CONFIGURED:" + ",".join(missing))
    if maker == "codex":
        routes["codex"] = GPTAdapter(CodexExecClient(), os.environ.get("BIE_CODEX_MODEL") or CODEX_MODEL)
    route = reviewer
    if reviewer and reviewer_model:
        same_model = reviewer_model == "same"
        if same_model and not same:
            raise SystemExit("SAME_MODEL_CHECKER_NEEDS_THE_SAME_PROVIDER")
        route = f"{reviewer}-checker" if same else reviewer
        if fake:
            client = BrainFakeClient(reviewer)
            model = routes[maker].model if same_model else "fake-" + reviewer_model.replace("/", "-")
        else:
            via, key = route_for(reviewer)
            client = make_client(reviewer, key, via=via, max_output_tokens=max_output_tokens, stream=True)
            model = routes[maker].model if same_model else reviewer_model
        if same and model == routes[maker].model and not same_model:
            raise SystemExit("MAKER_AND_REVIEWER_MUST_DIFFER: the checker needs another model than the maker "
                             "(or --reviewer-model same, the weakest check)")
        routes[route] = ADAPTERS[reviewer](client, model)
    extra = {"sleep": lambda s: None} if fake else {}
    return LiveGateway(routes, ledger=ledger, guard=guard, **extra), route


def page_total(pdf_bytes: bytes, spec: str | None) -> int:
    import pypdfium2 as pdfium

    from bie.brain.pages import parse_page_range
    document = pdfium.PdfDocument(pdf_bytes)
    try:
        count = len(document)
    finally:
        document.close()
    return len(parse_page_range(spec, count))


GRACEFUL = ("stopped", "stopped: budget", "stopped: plan limit")


def chapter_pages(chapter: dict) -> int:
    return len(chapter.get("pages") or []) or int(chapter.get("page_count") or 1)


def stop_status(guard) -> str:
    reason = guard.stop_reason or ""
    if reason.startswith("plan_limit"):
        return "stopped: plan limit"
    return "stopped: balance" if reason.startswith("balance") else "stopped: budget"


def plan_usage(gateway) -> dict:
    """The plan usage of every subscription route (Codex), numbers only."""
    return {route: adapter.client.plan_usage() for route, adapter in gateway.routes.items()
            if callable(getattr(getattr(adapter, "client", None), "plan_usage", None))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--section", choices=("understand", "lesson", "director", "notes", "game", "visual", "chain"), default="understand")
    parser.add_argument("--source", help="chapter PDF (understand, chain)")
    parser.add_argument("--chapter-map", help="chapter_map.json from an earlier run (lesson)")
    parser.add_argument("--from-run", help="folder or https URL of an earlier run with chapter_map.json and lesson_plan.json (director)")
    parser.add_argument("--resume-from", help="folder or https URL of an earlier understand/chain run: its passed pages are reused")
    parser.add_argument("--videos", default="", help="visual: only these video ids, for example v1,v2")
    parser.add_argument("--render", action="store_true", help="visual: also render a silent MP4 preview of every video")
    parser.add_argument("--with-visual", action="store_true", help="chain: also run Section 4")
    parser.add_argument("--pages")
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--subject", default="")
    parser.add_argument("--learners", default="")
    parser.add_argument("--exam", default="")
    parser.add_argument("--language", default="Hinglish")
    parser.add_argument("--maker", choices=PROVIDERS + ("codex",), default="openai",
                        help="codex = GPT through the ChatGPT Pro plan with the Codex CLI (private machine only)")
    parser.add_argument("--reviewer", choices=PROVIDERS, default="google")
    parser.add_argument("--reviewer-model", default="", help="checker model; required when maker and reviewer are the same "
                                                             "provider (temporary same-company checker); 'same' = the maker's "
                                                             "model in a fresh call when the key allows only one model "
                                                             "(kamzor jaanch, marked same_model_temporary)")
    parser.add_argument("--max-inr", type=float, default=300.0, help="hard cost cap in rupees for this run (default 300)")
    parser.add_argument("--models", default="", help="for example anthropic=anthropic/claude-opus-5.5")
    parser.add_argument("--routes", default="", help="for example anthropic=aicredits")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--max-output-tokens", type=int, default=32000)
    parser.add_argument("--course", default="", help="title=...;subject=...;learners=...;exam=...;language=... (overrides)")
    parser.add_argument("--fake", action="store_true")
    args = parser.parse_args(argv)
    for pair in filter(None, (part.strip() for part in args.course.split(";"))):
        key, sep, value = pair.partition("=")
        if not sep or key.strip() not in ("title", "subject", "learners", "exam", "language"):
            raise SystemExit("BAD_COURSE_FIELD:" + pair)
        setattr(args, key.strip(), value.strip())
    if args.maker == args.reviewer and not args.reviewer_model:
        raise SystemExit("MAKER_AND_REVIEWER_MUST_DIFFER")
    if args.max_inr <= 0:
        raise SystemExit("MAX_INR_MUST_BE_POSITIVE")
    apply_overrides(args.models, MODEL_ENV, "MODEL")
    apply_overrides(args.routes, VIA_ENV, "ROUTE")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    secrets = all_keys()
    ledger = UsageLedger(out / "LEDGER.jsonl")
    summary = {"section": args.section, "fake": args.fake, "maker": args.maker, "reviewer": args.reviewer}
    rate = usd_inr()
    guard = CostGuard(args.max_inr, rate=rate)
    pages = 0
    try:
        gateway, reviewer = build_gateway(args.maker, args.reviewer, fake=args.fake, ledger=ledger,
                                          max_output_tokens=args.max_output_tokens, reviewer_model=args.reviewer_model,
                                          guard=guard)
        summary["models"] = {route: gateway.model_of(route) for route in gateway.routes}
        book = rulebook_module.load()
        runner = SectionRunner(gateway, maker=args.maker, reviewer=reviewer, rulebook=book, records_dir=out / "records")
        summary.update(reviewer_route=reviewer, reviewer_independence=runner.independence)
        course = Course(title=args.title or "Chapter", subject=args.subject or "as in the chapter",
                        learners=args.learners or "learners of this book", exam=args.exam or "their exam", language=args.language)
        summary.update(status="ok", rulebook=book.version)
        # Inputs first, so the estimate knows the page count.
        if args.section in ("understand", "chain"):
            if not args.source:
                raise SystemExit("SOURCE_REQUIRED")
            pdf = read_source(args.source)
            pages = page_total(pdf, args.pages)
            previous = json.loads(read_text(args.resume_from.rstrip("/") + "/chapter_map.json")) if args.resume_from else None
            if previous and previous.get("source_sha256") == hashlib.sha256(pdf).hexdigest():
                selected = set(parse_page_range(args.pages, previous.get("page_count") or pages))
                reused = sum(1 for p in previous.get("pages") or [] if p.get("status") == "passed" and p["page"] in selected)
                summary["resume"] = {"pages_reused": reused, "pages_to_run": pages - reused}
        elif args.section in ("lesson", "notes", "game"):
            if not args.chapter_map:
                raise SystemExit("CHAPTER_MAP_REQUIRED")
            chapter = json.loads(read_text(args.chapter_map))
            course = Course(**chapter["course"]) if not args.course else course
            pages = chapter_pages(chapter)
        else:
            if not args.from_run:
                raise SystemExit("FROM_RUN_REQUIRED")
            base = args.from_run.rstrip("/") + "/"
            chapter = json.loads(read_text(base + "chapter_map.json"))
            lesson = json.loads(read_text(base + "lesson_plan.json"))
            if args.section == "visual":
                director = json.loads(read_text(base + "director.json"))
            course = Course(**chapter["course"]) if not args.course else course
            pages = chapter_pages(chapter)
        maker_via = getattr(getattr(gateway.routes[args.maker], "client", None), "via", "direct")
        estimate = cost_module.estimate(args.section, summary.get("resume", {}).get("pages_to_run", pages), rate=rate,
                                        maker_model=gateway.model_of(args.maker), reviewer_model=gateway.model_of(reviewer),
                                        with_visual=args.with_visual, maker_subscription=maker_via in SUBSCRIPTION_VIAS)
        summary["estimate"] = estimate
        notice("pahra andaaza", cost_module.estimate_line(estimate, args.max_inr),
               "warning" if estimate["total_inr"] > args.max_inr else "notice")
        checked = preflight(gateway, vision=args.section in ("understand", "chain", "visual"))
        summary["preflight"] = checked
        for route, entry in checked["routes"].items():
            if entry["status"] != "ok":
                notice(f"pahra preflight {route}", redact(preflight_message(route, entry), secrets), "error")
            elif entry.get("wallet"):
                notice(f"pahra wallet {route}", redact(json.dumps(entry["wallet"]), secrets))
            if entry.get("plan_usage_before"):
                notice(f"pahra plan {route}", "before the run: " + redact(json.dumps(entry["plan_usage_before"]), secrets))
        if not checked["passed"]:
            summary.update(status="stopped: preflight",
                           error="a preflight call failed, so no section was run (see the pahra preflight annotations)")
        if args.section in ("understand", "chain") and summary["status"] == "ok":
            chapter = run_chapter(pdf, course, runner, out, pages=args.pages, workers=args.workers,
                                  max_rounds=args.max_rounds, previous_chapter=previous, max_output_tokens=args.max_output_tokens)
            summary.update(quality=chapter["quality"], map_status=chapter["map_status"],
                           pages=[{k: p[k] for k in ("page", "status", "rounds", "reused", "cost_usd", "seconds")} for p in chapter["pages"]])
            if guard.stopped:
                summary.update(status=stop_status(guard), stop_reason=guard.stop_reason)
            elif args.section == "chain" and chapter["map_status"] != "passed":
                summary.update(status="stopped", error="the chapter map did not pass, so the lesson and director were not run")
        if args.section in ("notes", "chain") and summary["status"] == "ok":
            notes = run_notes(chapter, course, runner, out, workers=args.workers, max_rounds=args.max_rounds)
            summary.update(notes_quality=notes["quality"])
        if guard.stopped and summary["status"] == "ok":
            summary.update(status=stop_status(guard), stop_reason=guard.stop_reason)
        if args.section in ("game", "chain") and summary["status"] == "ok":
            game = run_game_design(chapter, course, runner, out, max_rounds=args.max_rounds)
            summary.update(game_quality=game["quality"])
        if guard.stopped and summary["status"] == "ok":
            summary.update(status=stop_status(guard), stop_reason=guard.stop_reason)
        if args.section in ("lesson", "chain") and summary["status"] == "ok":
            lesson = run_lesson(chapter, course, runner, out, workers=args.workers, max_rounds=args.max_rounds,
                                max_output_tokens=args.max_output_tokens)
            summary.update(lesson_quality=lesson["quality"],
                           videos=[{k: v[k] for k in ("video_id", "status", "rounds", "cost_usd")} for v in lesson["videos"]])
            if guard.stopped:
                summary.update(status=stop_status(guard), stop_reason=guard.stop_reason)
            elif args.section == "chain" and not lesson["quality"]["videos_passed"]:
                summary.update(status="stopped", error="no lesson script passed, so the director was not run")
        if args.section in ("director", "chain") and summary["status"] == "ok":
            director = run_director(chapter, lesson, course, runner, out, workers=args.workers, max_rounds=args.max_rounds)
            summary.update(director_quality=director["quality"])
        if guard.stopped and summary["status"] == "ok":
            summary.update(status=stop_status(guard), stop_reason=guard.stop_reason)
        if summary["status"] == "ok" and (args.section == "visual" or (args.section == "chain" and args.with_visual)):
            wanted = {v.strip() for v in args.videos.split(",") if v.strip()}
            if wanted:
                director = dict(director, videos=[v for v in director["videos"] if v["video_id"] in wanted])
            visual = run_visual(chapter, lesson, director, course, runner, out, workers=args.workers, max_rounds=args.max_rounds)
            summary.update(visual_quality=visual["quality"])
            if guard.stopped:
                summary.update(status=stop_status(guard), stop_reason=guard.stop_reason)
            if args.render:
                from bie.brain.video.render import RenderError, mp4
                (out / "videos").mkdir(exist_ok=True)
                for spec_path in sorted((out / "video_specs").glob("*.json")):
                    try:
                        mp4(json.loads(spec_path.read_text(encoding="utf-8")), out / "videos" / (spec_path.stem + ".mp4"),
                            dist=out / "_preview", assets=out / "assets")
                    except RenderError as exc:
                        summary.setdefault("render_errors", []).append(f"{spec_path.stem}: {str(exc)[:300]}")
    except SystemExit:
        raise
    except Exception as exc:  # report every failure without leaking a key
        summary.update(status="failed", error=redact(f"{type(exc).__name__}: {exc}", secrets)[:500])
    summary["ledger_calls"] = len(ledger.rows)
    summary["ledger_cost_usd"] = round(sum(r.get("cost_usd") or 0.0 for r in ledger.rows), 6)
    summary["cost"] = dict(cost_module.actual(ledger.rows, pages=summary.get("resume", {}).get("pages_to_run", pages), rate=rate),
                           cap=guard.report(), note=COST_NOTE, real_bill_inr=None)
    if "gateway" in locals():
        after = plan_usage(gateway)
        if after:
            summary["plan_usage_after"] = after
            notice("pahra plan", "after the run: " + redact(json.dumps(after), secrets))
    text = redact(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False), secrets)
    (out / "SUMMARY.json").write_text(text + "\n", encoding="utf-8")
    spent = summary["cost"]
    notice("pahra kharch", f"Kharch Rs {spent['total_inr']:g}" + (f" (Rs {spent['inr_per_page']:g} per page, {pages} pages)" if pages else "")
           + f", seema Rs {args.max_inr:g}; " + ", ".join(f"{k} Rs {v['inr']:g}" for k, v in spent["sections"].items())
           + ". Ledger estimate, not the bill.", "warning" if guard.stopped else "notice")
    level = ("notice" if summary["status"] == "ok" else "warning" if summary["status"] in GRACEFUL else "error")
    notice("bie brain " + args.section, redact(json.dumps({k: summary.get(k) for k in
                                                         ("status", "stop_reason", "quality", "map_status", "notes_quality",
                                                          "game_quality", "lesson_quality", "director_quality",
                                                          "visual_quality", "render_errors", "ledger_cost_usd", "error")},
                                                        ensure_ascii=False), secrets), level)
    return 0 if summary["status"] == "ok" or summary["status"] in GRACEFUL else 1


if __name__ == "__main__":
    raise SystemExit(main())
