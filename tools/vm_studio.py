"""The course studio on Navin's Codex machine (VM job section ``studio``; Navin, 18 November 2026).

    python -B tools/vm_studio.py --stage questions --source <chapter PDF: https URL or file> --out <folder>
           [--pages 1-30] [--course "Class 11 Geography, NCERT level"] [--language Hinglish] [--max-rounds 3]

Stage ``questions`` (``bie.brain.studio``): the chapter's student questions, pillars and per-question film and game plan,
checked by code against every teachable block of the chapter; Navin says yes to the list before the films are made.
The maker is Codex on the ChatGPT plan (read-only, no shell, no files: the chapter text goes in the message), so no
rupees are billed; the plan's usage is read before and after.

Writes ``questions.json``, ``QUESTIONS.md`` (the list for Navin), ``record.json`` (rounds and problems) and
``SUMMARY.json`` (what the job runner reports).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import studio  # noqa: E402

STAGES = ("questions",)
MAX_PDF_BYTES = 120 * 1024 * 1024


def read_pdf(source: str) -> bytes:
    if source.startswith("https://"):
        import urllib.request
        request = urllib.request.Request(source, headers={"user-agent": "bie-studio/1"})
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read(MAX_PDF_BYTES + 1)
    else:
        data = Path(source).read_bytes()
    if len(data) > MAX_PDF_BYTES:
        raise ValueError("the PDF is larger than 120 MB")
    if not data.startswith(b"%PDF"):
        raise ValueError("the source is not a PDF")
    return data


def run(args, *, client=None, load=None) -> dict:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    summary = {"schema": "bie.studio-run/1", "section": "studio", "stage": args.stage, "status": "failed",
               "maker": "codex on the ChatGPT plan (read-only, no shell)", "cost": {"total_inr": 0.0}, "error": None}
    try:
        if client is None:
            from bie.model_gateway.live.codex_client import DEFAULT_MODEL, CodexExecClient
            client = CodexExecClient()
            model = args.model or DEFAULT_MODEL
        else:
            model = args.model or "fake"
        if load is None:
            from bie.brain.pages import load_pages
            load = load_pages
        summary["plan_usage_before"] = _usage(client)
        source_hash, page_count, pages = load(read_pdf(args.source), args.pages or None, with_images=False)
        summary.update(source_sha256=source_hash, page_count=page_count, pages_read=[p.number for p in pages])
        record = studio.plan(client, model, pages, course=args.course, language=args.language,
                             max_rounds=args.max_rounds)
        (out / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        if isinstance(record.get("answer"), dict):
            (out / "questions.json").write_text(json.dumps(record["answer"], ensure_ascii=False, indent=1), encoding="utf-8")
        (out / "QUESTIONS.md").write_text(studio.markdown(record), encoding="utf-8")
        answer = record.get("answer") or {}
        summary.update(status="ok" if not record["problems"] else "needs_fix", rounds=len(record["rounds"]),
                       problems=record["problems"], coverage={k: v for k, v in (record.get("coverage") or {}).items()
                                                              if k != "missing"},
                       questions=len(answer.get("questions") or []), pillars=len(answer.get("pillars") or []),
                       usage=record["usage"], model=model)
        summary["plan_usage_after"] = _usage(client)
    except Exception as exc:                        # the runner publishes the folder either way; the error says why
        summary["error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
        kind = getattr(exc, "kind", None)
        if kind == "plan_limit":
            summary["stop_reason"] = "plan_limit"
    summary["minutes"] = round((time.time() - started) / 60, 1)
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def _usage(client):
    reader = getattr(client, "plan_usage", None)
    return reader() if callable(reader) else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", choices=STAGES, default="questions")
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--pages", default="")
    parser.add_argument("--course", default="")
    parser.add_argument("--language", default="Hinglish")
    parser.add_argument("--model", default="")
    parser.add_argument("--max-rounds", type=int, default=3)
    args = parser.parse_args(argv)
    args.max_rounds = max(1, min(6, args.max_rounds))
    summary = run(args)
    print(json.dumps({k: summary.get(k) for k in ("status", "questions", "coverage", "error")}, ensure_ascii=False))
    return 0 if summary["status"] in ("ok", "needs_fix") else 1


if __name__ == "__main__":
    raise SystemExit(main())
