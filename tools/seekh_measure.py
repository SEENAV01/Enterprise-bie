"""Measure live runs the same way every time, for the seekh log (docs/roadmap/SEEKH_LOG.md).

  python tools/seekh_measure.py <run folder> [<run folder> ...] [--json]

Reads each folder's process records (``records/*.json``) and ``SUMMARY.json`` and reports, per step (page reading,
chapter map, prerequisite trim, lesson plan, scripts): units and how many passed, first-try pass (passed in round 1), rounds per unit,
maker and checker tokens per unit, rupees per unit (the checker on the API; a maker on a subscription is ₹0), minutes
per unit, what sent round 1 back (BIE's code problems, grouped with their ids removed) and the reviewer's findings by
severity. Folders are read in order and a unit in a later folder replaces the same unit of an earlier one (a resumed run
after the run it resumed). Nothing is sent to any model.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

STEPS = ("pages", "map", "trim", "plan", "scripts")
FINDING_KEYS = ("missing", "wrong", "shallow", "problems")
IDS = re.compile(r"\bp\d{3,4}-[ib]\d+\b|\b[icbvq]\d+(?:\.\d+)?\b")     # p013-i1, p0005-b0021, i21, c34, c1.1, v2
QUOTED = re.compile(r"'[^']{13,}'|\"[^\"]{13,}\"")                    # a quoted question or sentence, not 'none'


def step_of(record: dict) -> str:
    section, unit = record.get("section"), record.get("unit", "")
    if section == "understand":
        return "pages"
    if section == "connect":
        return "trim" if unit == "prerequisites" else "map"
    if section == "lesson":
        return "plan" if unit == "plan" else "scripts"
    return section or "other"


def problem_kind(text: str) -> str:
    """A code problem without its ids and quoted words, so the same problem on two units counts as one kind."""
    text = text.replace("[code] ", "").strip()
    return IDS.sub("_", QUOTED.sub("'…'", text))[:140]


def units(folders) -> dict:
    """{(step, unit): (record, usd_inr)} with later folders replacing earlier ones."""
    out = {}
    for folder in folders:
        folder = Path(folder)
        try:
            rate = json.loads((folder / "SUMMARY.json").read_text(encoding="utf-8"))["cost"]["usd_inr"]
        except (OSError, ValueError, KeyError, TypeError):
            rate = None
        for path in sorted((folder / "records").glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            out[(step_of(record), record.get("unit", path.stem))] = (record, rate)
    return out


def measure(folders) -> dict:
    groups = {}
    for (step, unit), (record, rate) in units(folders).items():
        groups.setdefault(step, []).append((unit, record, rate))
    result = {}
    for step, rows in groups.items():
        n = len(rows)
        rounds = [len(r["rounds"]) for _, r, _ in rows]
        continued = [u for u, r, _ in rows if r["rounds"] and r["rounds"][0].get("mode") == "resume"]   # round 0: an earlier answer
        first = [u for u, r, _ in rows if r["status"] == "passed" and len(r["rounds"]) == 1 and u not in continued]
        maker_in = sum((rd.get("maker") or {}).get("input_tokens", 0) for _, r, _ in rows for rd in r["rounds"])
        maker_out = sum((rd.get("maker") or {}).get("output_tokens", 0) for _, r, _ in rows for rd in r["rounds"])
        check_in = sum((rd.get("review") or {}).get("input_tokens", 0) for _, r, _ in rows for rd in r["rounds"])
        check_out = sum((rd.get("review") or {}).get("output_tokens", 0) for _, r, _ in rows for rd in r["rounds"])
        inr = [r.get("cost_usd", 0.0) * rate for _, r, rate in rows if rate]
        round_one = Counter(problem_kind(p) for _, r, _ in rows for p in (r["rounds"][0].get("code_problems") or []))
        severity, kinds = Counter(), Counter()
        for _, r, _ in rows:
            for rd in r["rounds"]:
                value = (rd.get("review") or {}).get("value") or {}
                for key in FINDING_KEYS:
                    for finding in value.get(key) or []:
                        severity[finding.get("severity", "blocking")] += 1
                        kinds[key] += 1
        result[step] = {
            "units": n, "passed": sum(1 for _, r, _ in rows if r["status"] == "passed"), "continued": len(continued),
            "first_try": len(first), "first_try_rate": round(len(first) / n, 3) if n else None,
            "rounds_per_unit": round(sum(rounds) / n, 2) if n else None,
            "maker_tokens_per_unit": [round(maker_in / n), round(maker_out / n)] if n else None,
            "checker_tokens_per_unit": [round(check_in / n), round(check_out / n)] if n else None,
            "inr_per_unit": round(sum(inr) / len(inr), 2) if inr else None, "inr_total": round(sum(inr), 2) if inr else None,
            "minutes_per_unit": round(sum(r.get("seconds", 0.0) for _, r, _ in rows) / n / 60, 1) if n else None,
            "round_one_code_problems": dict(round_one.most_common(8)),
            "reviewer_findings": dict(severity), "reviewer_finding_kinds": dict(kinds),
            "not_passed": sorted(u for u, r, _ in rows if r["status"] != "passed"),
        }
    return {step: result[step] for step in sorted(result, key=lambda s: STEPS.index(s) if s in STEPS else len(STEPS))}


def markdown(result: dict) -> str:
    steps = list(result)
    lines = ["| Measure | " + " | ".join(steps) + " |", "| --- |" + " --- |" * len(steps)]

    def row(name, fn):
        lines.append(f"| {name} | " + " | ".join(fn(result[s]) for s in steps) + " |")

    row("Units passed", lambda m: f"{m['passed']} of {m['units']}")
    row("First-try pass", lambda m: f"{m['first_try']} of {m['units']} ({m['first_try_rate']:.0%})")
    if any(result[s].get("continued") for s in steps):
        row("Continued from an earlier answer", lambda m: f"{m.get('continued', 0)} of {m['units']}")
    row("Rounds per unit", lambda m: f"{m['rounds_per_unit']}")
    row("Maker tokens per unit (in · out)", lambda m: "{:,} · {:,}".format(*m["maker_tokens_per_unit"]))
    row("Checker tokens per unit (in · out)", lambda m: "{:,} · {:,}".format(*m["checker_tokens_per_unit"]))
    row("₹ per unit (checker)", lambda m: "—" if m["inr_per_unit"] is None else f"₹{m['inr_per_unit']:.2f}")
    row("Minutes per unit", lambda m: f"{m['minutes_per_unit']}")
    row("Reviewer findings", lambda m: ", ".join(f"{k} {v}" for k, v in sorted(m["reviewer_findings"].items())) or "none")
    out = "\n".join(lines) + "\n"
    for step in steps:
        problems = result[step]["round_one_code_problems"]
        if problems:
            out += f"\nRound 1 sent back ({step}): " + "; ".join(f"{k} ×{v}" for k, v in problems.items()) + "\n"
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folders", type=Path, nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    missing = [str(f) for f in args.folders if not (f / "records").is_dir()]
    if missing:
        raise SystemExit("NO_RECORDS: " + ", ".join(missing))
    result = measure(args.folders)
    print(json.dumps(result, ensure_ascii=False, indent=1) if args.json else markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
