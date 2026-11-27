"""BIE's checks on one heading of a chapter script, for the script writer's self-check (Navin, 26 November 2026: script
writing moved from Codex to Claude; `.claude/skills/bie-script-writer`). Prints BIE's own problems
(`studio_script.problems`, with the earlier headings of the same script as what was taught before), the voice measures
the gold standard is measured by, and, with ``--before``, how much the heading grew since an earlier version (fix rounds
that add sentences are patching).

    python3 tools/script_writer_check.py --script script.json --chapter chapter_map.json --heading 11.6.3 \
        [--before old_script.json] [--json out.json]

The problems are advice for the writer to weigh; BIE's script stage still runs its own checks on what is handed over.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bie.brain import studio_script  # noqa: E402

GROWTH = 0.15                 # a heading that grew more than this since its last version was probably patched


def voice(part: dict) -> dict:
    """The gold standard's measures: sentences, words per sentence, questions, the share spoken to the learner and the
    share going on the way a teacher talks, and sentences per listed fact (of every kind)."""
    said = [s for p in part.get("points") or [] for s in studio_script.sentences(p)]
    if not said:
        return {"sentences": 0}
    words = [len(s.split()) for s in said]
    facts = [f for f in part.get("facts") or [] if isinstance(f, dict)]
    return {"sentences": len(said), "words_per_sentence": round(statistics.mean(words), 1),
            "questions": sum(s.rstrip().endswith("?") for s in said),
            "talk_share": round(sum(bool(studio_script.TALK.search(s)) for s in said) / len(said), 2),
            "flow_share": round(sum(bool(studio_script.FLOW.search(s)) for s in said) / len(said), 2),
            "sentences_per_fact": round(len(said) / len(facts), 1) if facts else None}


def check(script: dict, chapter: dict, number: str, before: dict | None = None) -> dict:
    heads = studio_script.headings(chapter)
    order = [h["number"] for h in heads]
    if number not in order:
        raise SystemExit(f"heading {number} is not in the chapter file ({', '.join(order)})")
    n = order.index(number)
    part = next((p for p in script.get("parts") or [] if p.get("section") == number), None)
    if part is None:
        raise SystemExit(f"heading {number} is not in the script")
    earlier = [p for p in script.get("parts") or [] if p.get("section") in order[:n]]
    later = [t for h in heads[n + 1:] for t, _ in studio_script.first_terms(h) if studio_script._technical(t)]
    out = {"heading": number, "problems": studio_script.problems(part, heads[n], chapter, earlier, later),
           "voice": voice(part)}
    old = next((p for p in (before or {}).get("parts") or [] if p.get("section") == number), None)
    if old is not None:
        was, now = voice(old).get("sentences") or 0, out["voice"].get("sentences") or 0
        grew = (now - was) / was if was else 0.0
        out["growth"] = {"before": was, "now": now, "share": round(grew, 2), "patching": grew > GROWTH}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--script", required=True)
    parser.add_argument("--chapter", required=True, help="the chapter map (chapter_map.json)")
    parser.add_argument("--heading", required=True)
    parser.add_argument("--before", default="", help="an earlier version of the script, to see how much the heading grew")
    parser.add_argument("--json", default="", help="also write the result here")
    args = parser.parse_args(argv)
    read = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))  # noqa: E731
    result = check(read(args.script), read(args.chapter), args.heading, read(args.before) if args.before else None)
    v = result["voice"]
    print(f"{result['heading']}: {v.get('sentences')} sentences, {v.get('words_per_sentence')} words each, "
          f"{v.get('questions')} questions, {v.get('talk_share')} spoken to the learner, {v.get('flow_share')} going on, "
          f"{v.get('sentences_per_fact')} sentences per fact (gold standard: about 15 words, a quarter "
          "spoken to the learner, about 2.4 sentences per fact)")
    if "growth" in result:
        g = result["growth"]
        print(f"grew {g['before']} -> {g['now']} sentences ({g['share']:+.0%})"
              + ("; that is patching: write the grown blocks again as one flow" if g["patching"] else ""))
    print(f"{len(result['problems'])} problems (advice to weigh; fix by rewording, not adding):")
    for line in result["problems"]:
        print(" -", line)
    if args.json:
        Path(args.json).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
