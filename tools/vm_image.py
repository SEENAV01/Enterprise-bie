"""Images through the ChatGPT plan on Navin's Codex machine (Task 046 one-shot test, Navin 26 October 2026).

    python -B tools/vm_image.py --prompts <https URL or file of bie.image-prompts/1> --out <folder> [--max-images 4]

BIE writes the prompts (the one-shot's prompt writer turns a shot into an image description; nothing is written by
hand); this tool only makes the pictures: one ``codex exec`` per prompt with Codex's built-in ``image_gen`` tool
(gpt-image-2 behind it), signed in with the plan, no API key. It reads the plan's usage before the first image and
after the last (image generation uses the plan's limits several times faster than text), writes
``images/<id>.<png|jpg|webp>``, ``prompts.json``, ``IMAGES.md`` and ``SUMMARY.json``, and stops at a used-up plan
window as "stopped: plan limit". The VM runner (``tools/codex_vm.py``, section ``image``) publishes the folder to
``blindtest-results``. Billed in rupees: nothing (the plan).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.model_gateway.live.codex_client import CodexExecClient  # noqa: E402
from bie.model_gateway.live.errors import ProviderError  # noqa: E402

SCHEMA = "bie.image-prompts/1"
ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
MAX_IMAGES = 4


def read_source(source: str) -> str:
    from run_brain import read_text
    return read_text(source)


def load_prompts(text: str, max_images: int = MAX_IMAGES) -> dict:
    """The prompt file, checked: schema, 1..max prompts, ids, prompt length, no control characters."""
    data = json.loads(text)
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"prompts: must be a {SCHEMA} object")
    prompts = data.get("prompts")
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= max_images:
        raise ValueError(f"prompts: 1 to {max_images} prompts")
    seen = set()
    for p in prompts:
        if not isinstance(p, dict) or not ID.match(str(p.get("id", ""))) or p["id"] in seen:
            raise ValueError("prompts: every prompt needs a unique lowercase id")
        seen.add(p["id"])
        text_ = p.get("prompt")
        if not isinstance(text_, str) or not 40 <= len(text_) <= 4000 or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text_):
            raise ValueError(f"prompts: {p['id']} needs 40 to 4000 characters of plain text")
    return data


def run(prompts: dict, out: Path, *, client: CodexExecClient | None = None, model: str | None = None) -> dict:
    client = client or CodexExecClient()
    out.mkdir(parents=True, exist_ok=True)
    (out / "prompts.json").write_text(json.dumps(prompts, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {"schema": "bie.vm-image-run/1", "section": "image", "maker": "codex image_gen (ChatGPT plan, no API key)",
               "image_model": "gpt-image-2 behind Codex's built-in image_gen tool", "status": "ok", "stop_reason": None,
               "error": None, "images": [], "cost": {"total_inr": 0.0, "billing": "subscription",
                                                    "note": "billed to the ChatGPT plan; no rupees"}}
    login = client.login_status()
    summary["login"] = login
    if not login.get("logged_in"):
        summary.update(status="stopped: not signed in", error="codex is not signed in on this machine")
        return finish(out, summary)
    summary["plan_usage_before"] = client.plan_usage()
    started = time.time()
    for p in prompts["prompts"]:
        row = {"id": p["id"]}
        try:
            row.update(client.generate_image(p["prompt"], out / "images" / p["id"], model=model))
            row["status"] = "made"
        except ProviderError as exc:
            row.update(status="failed", error=f"{exc.kind}: {str(exc)[-240:]}")
            summary["images"].append(row)
            if exc.kind == "plan_limit":
                summary.update(status="stopped: plan limit", stop_reason=row["error"])
                break
            continue
        summary["images"].append(row)
    summary["plan_usage_after"] = client.plan_usage()
    summary["minutes"] = round((time.time() - started) / 60, 2)
    made = [r for r in summary["images"] if r["status"] == "made"]
    if not made and summary["status"] == "ok":
        summary.update(status="failed", error="no image was made")
    return finish(out, summary)


def finish(out: Path, summary: dict) -> dict:
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# Images through the ChatGPT plan", "", f"status: {summary['status']}", ""]
    for r in summary["images"]:
        lines.append(f"- {r['id']}: {r['status']}" + (f", {r.get('file')}, {r.get('bytes')} bytes, {r.get('seconds')} s, found by "
                                                      f"{r.get('found_by')}" if r["status"] == "made" else f" ({r.get('error')})"))
    lines += ["", "Plan usage before: " + json.dumps(summary.get("plan_usage_before")),
              "Plan usage after: " + json.dumps(summary.get("plan_usage_after")), ""]
    (out / "IMAGES.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: summary.get(k) for k in ("status", "stop_reason", "error")}
                     | {"made": sum(1 for r in summary["images"] if r["status"] == "made")}), flush=True)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-images", type=int, default=MAX_IMAGES)
    parser.add_argument("--model", default="")
    args = parser.parse_args(argv)
    out = Path(args.out)
    try:
        prompts = load_prompts(read_source(args.prompts), max(1, min(MAX_IMAGES, args.max_images)))
    except (ValueError, OSError) as exc:
        out.mkdir(parents=True, exist_ok=True)
        finish(out, {"section": "image", "status": "refused", "error": str(exc)[:300], "images": [], "stop_reason": None,
                     "cost": {"total_inr": 0.0}})
        return 2
    summary = run(prompts, out, model=args.model or None)
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
