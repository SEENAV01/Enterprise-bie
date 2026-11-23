"""Put a passed film's aatma into the almaari, after Navin's yes (Navin, 23 November 2026).

    python -B tools/lock_aatma.py --run <films run: folder or https URL> --qid h11-6-3b --by "Navin, 24 November 2026" \
        [--words "bolte huye screen par wahi step par dhyan jata hai"] [--only naam_par_chale,ek_ek_step]
    python -B tools/lock_aatma.py --page --run <films run> --qid h11-6-3b --out <page .html>

``--page`` writes the film's review page "Is film ki aatma" (the forms BIE found, in general words, with this film's
filling and its measures) for Navin to read before he says yes. Without ``--page`` the film's forms are locked into
``bie/brain/rulebook/aatma.json`` with the run, his words and who locked them; the file's version goes up. Only Navin's
yes on a BIE film locks; Claude runs this after it and never on its own, and never for a demo. The change is a reviewed
PR like any rulebook change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import aatma  # noqa: E402


def film_of(run: str, qid: str) -> tuple:
    from vm_studio import read_json
    record = read_json(run, f"films/{qid}.json")
    try:
        questions = read_json(run, "questions.json")
    except Exception:                                   # a run without its questions still has its film
        questions = {}
    question = next((q for q in (questions.get("questions") or []) if q.get("id") == qid), {"id": qid})
    return record["film"], question, questions.get("chapter_title", "")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True)
    parser.add_argument("--qid", required=True)
    parser.add_argument("--page", action="store_true", help="write the review page instead of locking")
    parser.add_argument("--out", default="")
    parser.add_argument("--by", default="", help="who said yes, and when (required to lock)")
    parser.add_argument("--words", default="", help="Navin's own words on why the film worked")
    parser.add_argument("--only", default="", help="lock only these form ids (comma separated)")
    parser.add_argument("--book", default=str(aatma.PATH))
    args = parser.parse_args(argv)
    film, question, chapter = film_of(args.run, args.qid)
    if args.page:
        if not args.out:
            parser.error("--page needs --out")
        Path(args.out).write_text(aatma.page(film, question=question, chapter=chapter), encoding="utf-8")
        print(f"page: {args.out}")
        return 0
    if not args.by.strip():
        parser.error("locking needs --by: Navin's yes and its date")
    book_path = Path(args.book)
    book = json.loads(book_path.read_text(encoding="utf-8")) if book_path.exists() else aatma.almaari()
    only = [x.strip() for x in args.only.split(",") if x.strip()] or None
    new = aatma.lock(book, film, qid=args.qid, run=args.run, by=args.by, words=args.words, only=only)
    book_path.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    entry = new["films"][-1]
    print(f"locked {len(entry['forms'])} forms of {args.qid} (almaari version {new['version']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
