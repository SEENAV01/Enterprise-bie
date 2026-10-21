"""Run BIE brain sections on a real chapter.

  --section understand   Section 1: the chapter PDF → chapter_map.json, MAP.md
  --section lesson       Section 2: a chapter map (--chapter-map, path or https URL) → lesson_plan.json, SCRIPT.md
  --section director     Section 3: --from-run (folder or URL with chapter_map.json and lesson_plan.json) → director.json
  --section chain        Sections 1, 2 and 3 in one run

  python tools/run_brain.py --section understand --source <pdf path or https URL> --out <dir> \
      --title "10. Tissues and Its Types" --subject "Science and Technology" --learners "UPSC / State PCS aspirants" \
      --exam "UPSC / State PCS" --language Hinglish --maker anthropic --reviewer openai

Keys come only from environment variables (GitHub Actions secrets). The maker and the reviewer must be
different providers. Outputs in --out: chapter_map.json, MAP.md, records/ (one process record per step,
images by hash only), LEDGER.jsonl (every provider call with tokens and estimated cost) and
SUMMARY.json (also printed as ::notice annotations). --fake runs offline with the deterministic
brain fake.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import rulebook as rulebook_module  # noqa: E402
from bie.brain.fake import BrainFakeClient  # noqa: E402
from bie.brain.runner import SectionRunner  # noqa: E402
from bie.brain.director import run_director  # noqa: E402
from bie.brain.lesson import run_lesson  # noqa: E402
from bie.brain.understanding import Course, run_chapter  # noqa: E402
from bie.model_gateway.live.config import ADAPTERS, MODEL_ENV, PROVIDERS, VIA_ENV, all_keys, build_routes  # noqa: E402
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


def build_gateway(maker, reviewer, *, fake, ledger, max_output_tokens):
    providers = [p for p in (maker, reviewer) if p]
    if fake:
        routes = {p: ADAPTERS[p](BrainFakeClient(p), f"fake-{p}") for p in providers}
        return LiveGateway(routes, ledger=ledger, sleep=lambda s: None)
    routes, missing = build_routes(providers, max_output_tokens=max_output_tokens, stream=True)
    if missing:
        raise SystemExit("NOT_CONFIGURED:" + ",".join(missing))
    return LiveGateway(routes, ledger=ledger)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--section", choices=("understand", "lesson", "director", "chain"), default="understand")
    parser.add_argument("--source", help="chapter PDF (understand, chain)")
    parser.add_argument("--chapter-map", help="chapter_map.json from an earlier run (lesson)")
    parser.add_argument("--from-run", help="folder or https URL of an earlier run with chapter_map.json and lesson_plan.json (director)")
    parser.add_argument("--resume-from", help="folder or https URL of an earlier understand/chain run: its passed pages are reused")
    parser.add_argument("--pages")
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--subject", default="")
    parser.add_argument("--learners", default="")
    parser.add_argument("--exam", default="")
    parser.add_argument("--language", default="Hinglish")
    parser.add_argument("--maker", choices=PROVIDERS, default="anthropic")
    parser.add_argument("--reviewer", choices=PROVIDERS, default="openai")
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
    if args.maker == args.reviewer:
        raise SystemExit("MAKER_AND_REVIEWER_MUST_DIFFER")
    apply_overrides(args.models, MODEL_ENV, "MODEL")
    apply_overrides(args.routes, VIA_ENV, "ROUTE")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    secrets = all_keys()
    ledger = UsageLedger(out / "LEDGER.jsonl")
    summary = {"section": args.section, "fake": args.fake, "maker": args.maker, "reviewer": args.reviewer}
    try:
        gateway = build_gateway(args.maker, args.reviewer, fake=args.fake, ledger=ledger,
                                max_output_tokens=args.max_output_tokens)
        summary["models"] = {route: gateway.model_of(route) for route in gateway.routes}
        book = rulebook_module.load()
        runner = SectionRunner(gateway, maker=args.maker, reviewer=args.reviewer, rulebook=book,
                               records_dir=out / "records")
        course = Course(title=args.title or "Chapter", subject=args.subject or "as in the chapter",
                        learners=args.learners or "learners of this book", exam=args.exam or "their exam", language=args.language)
        summary.update(status="ok", rulebook=book.version)
        if args.section in ("understand", "chain"):
            if not args.source:
                raise SystemExit("SOURCE_REQUIRED")
            previous = json.loads(read_text(args.resume_from.rstrip("/") + "/chapter_map.json")) if args.resume_from else None
            chapter = run_chapter(read_source(args.source), course, runner, out, pages=args.pages, workers=args.workers,
                                  max_rounds=args.max_rounds, previous_chapter=previous)
            summary.update(quality=chapter["quality"], map_status=chapter["map_status"],
                           pages=[{k: p[k] for k in ("page", "status", "rounds", "reused", "cost_usd")} for p in chapter["pages"]])
            if args.section == "chain" and chapter["map_status"] != "passed":
                summary.update(status="stopped", error="the chapter map did not pass, so the lesson and director were not run")
        elif args.section == "lesson":
            if not args.chapter_map:
                raise SystemExit("CHAPTER_MAP_REQUIRED")
            chapter = json.loads(read_text(args.chapter_map))
            course = Course(**chapter["course"]) if not args.course else course
        else:
            if not args.from_run:
                raise SystemExit("FROM_RUN_REQUIRED")
            base = args.from_run.rstrip("/") + "/"
            chapter = json.loads(read_text(base + "chapter_map.json"))
            lesson = json.loads(read_text(base + "lesson_plan.json"))
            course = Course(**chapter["course"]) if not args.course else course
        if args.section in ("lesson", "chain") and summary["status"] == "ok":
            lesson = run_lesson(chapter, course, runner, out, workers=args.workers, max_rounds=args.max_rounds)
            summary.update(lesson_quality=lesson["quality"],
                           videos=[{k: v[k] for k in ("video_id", "status", "rounds", "cost_usd")} for v in lesson["videos"]])
        if args.section == "chain" and summary["status"] == "ok" and not lesson["quality"]["videos_passed"]:
            summary.update(status="stopped", error="no lesson script passed, so the director was not run")
        if args.section in ("director", "chain") and summary["status"] == "ok":
            director = run_director(chapter, lesson, course, runner, out, workers=args.workers, max_rounds=args.max_rounds)
            summary.update(director_quality=director["quality"])
    except SystemExit:
        raise
    except Exception as exc:  # report every failure without leaking a key
        summary.update(status="failed", error=redact(f"{type(exc).__name__}: {exc}", secrets)[:500])
    summary["ledger_calls"] = len(ledger.rows)
    summary["ledger_cost_usd"] = round(sum(r.get("cost_usd") or 0.0 for r in ledger.rows), 6)
    text = json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False)
    (out / "SUMMARY.json").write_text(text + "\n", encoding="utf-8")
    notice("bie brain " + args.section, redact(json.dumps({k: summary.get(k) for k in
                                                         ("status", "quality", "map_status", "lesson_quality", "director_quality",
                                                          "ledger_cost_usd", "error")},
                                                        ensure_ascii=False), secrets),
           "notice" if summary["status"] == "ok" else "warning" if summary["status"] == "stopped" else "error")
    return 0 if summary["status"] in ("ok", "stopped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
