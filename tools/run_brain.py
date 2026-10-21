"""Run a BIE brain section on a real chapter (Task 039: Section 1, understanding the book).

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
from bie.brain.understanding import Course, run_chapter  # noqa: E402
from bie.model_gateway.live.config import ADAPTERS, MODEL_ENV, PROVIDERS, VIA_ENV, all_keys, build_routes  # noqa: E402
from bie.model_gateway.live.errors import redact  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402
from bie.model_gateway.live.ledger import UsageLedger  # noqa: E402
from run_blind_test import apply_overrides, notice, read_source  # noqa: E402


def build_gateway(maker, reviewer, *, fake, ledger, max_output_tokens):
    providers = [p for p in (maker, reviewer) if p]
    if fake:
        routes = {p: ADAPTERS[p](BrainFakeClient(p), f"fake-{p}") for p in providers}
        return LiveGateway(routes, ledger=ledger, sleep=lambda s: None)
    routes, missing = build_routes(providers, max_output_tokens=max_output_tokens)
    if missing:
        raise SystemExit("NOT_CONFIGURED:" + ",".join(missing))
    return LiveGateway(routes, ledger=ledger)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--section", choices=("understand",), default="understand")
    parser.add_argument("--source", required=True)
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
        data = read_source(args.source)
        gateway = build_gateway(args.maker, args.reviewer, fake=args.fake, ledger=ledger,
                                max_output_tokens=args.max_output_tokens)
        summary["models"] = {route: gateway.model_of(route) for route in gateway.routes}
        book = rulebook_module.load()
        runner = SectionRunner(gateway, maker=args.maker, reviewer=args.reviewer, rulebook=book,
                               records_dir=out / "records")
        course = Course(title=args.title or "Chapter", subject=args.subject or "as in the chapter",
                        learners=args.learners or "learners of this book", exam=args.exam or "their exam", language=args.language)
        chapter = run_chapter(data, course, runner, out, pages=args.pages, workers=args.workers, max_rounds=args.max_rounds)
        summary.update(status="ok", rulebook=book.version, quality=chapter["quality"],
                       pages=[{k: p[k] for k in ("page", "status", "rounds", "cost_usd")} for p in chapter["pages"]],
                       map_status=chapter["map_status"])
    except SystemExit:
        raise
    except Exception as exc:  # report every failure without leaking a key
        summary.update(status="failed", error=redact(f"{type(exc).__name__}: {exc}", secrets)[:500])
    summary["ledger_calls"] = len(ledger.rows)
    summary["ledger_cost_usd"] = round(sum(r.get("cost_usd") or 0.0 for r in ledger.rows), 6)
    text = json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False)
    (out / "SUMMARY.json").write_text(text + "\n", encoding="utf-8")
    notice("bie brain " + args.section, redact(json.dumps({k: summary.get(k) for k in
                                                         ("status", "quality", "map_status", "ledger_cost_usd", "error")},
                                                        ensure_ascii=False), secrets),
           "notice" if summary["status"] == "ok" else "error")
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
