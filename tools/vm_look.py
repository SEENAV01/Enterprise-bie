"""LOOK-01 on Navin's Codex machine: the look check with the free Google reviewer (Task 046 one-shot test).

    python -B tools/vm_look.py --request <https URL or file of bie.look-request/1> --out <folder> --max-inr 5
        [--models google=gemini-3.8-flash] [--routes google=direct]

The request names the shot, BIE's frames per route (https URLs of our renders on the blindtest-results branch, at most
3 per route) and the reference: ``private_set`` (a folder ``$BIE_HOME/private/refs/<name>/`` on this machine with up to
3 benchmark frames, which never leave it: they are not ours to publish) and a written ``description`` of the benchmark's
look, used when the private set is missing. One reviewer call per route, through the cost guard; the answers
(``look.json``), the ledger and ``SUMMARY.json`` go back through the VM runner (section ``look``). The reference frames
are recorded only by file name and SHA-256.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import look  # noqa: E402
from bie.model_gateway.live.budget import COST_NOTE, CostGuard, usd_inr  # noqa: E402
from bie.model_gateway.live.config import MODEL_ENV, VIA_ENV, build_routes  # noqa: E402
from bie.model_gateway.live.errors import ProviderError  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402
from bie.model_gateway.live.ledger import UsageLedger  # noqa: E402
from bie.model_gateway.model_interface import ModelRequest  # noqa: E402

SCHEMA = "bie.look-request/1"
FRAME_URL = re.compile(r"^https://raw\.githubusercontent\.com/SEENAV01/Enterprise-bie/blindtest-results/runs/[A-Za-z0-9._/-]{1,200}\.(png|jpg|jpeg)$")
SET_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{2,40}$")
ROUTE = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}$")
MAX_FRAMES = 3
MAX_BYTES = 6 * 1024 * 1024
MEDIA = {b"\x89PNG": "image/png", b"\xff\xd8\xff": "image/jpeg"}


def media_of(data: bytes) -> str:
    return next((m for magic, m in MEDIA.items() if data.startswith(magic)), "")


MAX_D1_PARTS = 40


def load_d1_request(data: dict) -> dict:
    """LOOK-D1 (Task 046 Part D1): {"rule": "LOOK-D1", "reviewer": "codex" | "google", "parts": [{"id", "point", "frame"}]},
    one still per part (at most 40), each a PNG or JPEG of our render on blindtest-results."""
    parts = data.get("parts")
    if not isinstance(parts, list) or not 1 <= len(parts) <= MAX_D1_PARTS:
        raise ValueError(f"parts: 1 to {MAX_D1_PARTS} parts")
    for part in parts:
        if not isinstance(part, dict) or not str(part.get("id") or "").strip() or not str(part.get("point") or "").strip():
            raise ValueError("parts: every part needs an id and a point")
        if not isinstance(part.get("frame"), str) or not FRAME_URL.match(part["frame"]):
            raise ValueError(f"parts: {part.get('id')}: the frame must be a PNG or JPEG file under blindtest-results/runs/")
    if data.get("reviewer", "codex") not in ("codex", "google"):
        raise ValueError("reviewer: codex or google")
    return data


def load_request(text: str) -> dict:
    data = json.loads(text)
    if isinstance(data, dict) and data.get("rule") == look.D1_RULE:
        if data.get("schema") != SCHEMA:
            raise ValueError(f"schema: must be {SCHEMA}")
        return load_d1_request(data)
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"request: must be a {SCHEMA} object")
    routes = data.get("routes")
    if not isinstance(routes, dict) or not 1 <= len(routes) <= 4:
        raise ValueError("routes: 1 to 4 routes")
    for name, urls in routes.items():
        if not ROUTE.match(name) or not isinstance(urls, list) or not 1 <= len(urls) <= MAX_FRAMES:
            raise ValueError(f"routes: {name!r} needs 1 to {MAX_FRAMES} frames")
        for url in urls:
            if not isinstance(url, str) or not FRAME_URL.match(url):
                raise ValueError(f"routes: {name}: frames must be PNG or JPEG files under blindtest-results/runs/")
    ref = data.get("reference") or {}
    if ref.get("private_set") and not SET_NAME.match(str(ref["private_set"])):
        raise ValueError("reference.private_set: a short lowercase name")
    if not str(ref.get("description") or "").strip():
        raise ValueError("reference.description: needed (used when the private set is missing)")
    if not str((data.get("shot") or {}).get("sentence") or "").strip():
        raise ValueError("shot.sentence: needed")
    return data


def fetch(url: str, opener=None) -> bytes:
    request = urllib.request.Request(url, headers={"user-agent": "bie-look/1"})
    with (opener or urllib.request.urlopen)(request, timeout=120) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or not media_of(data):
        raise ValueError(f"{url}: not a PNG or JPEG under {MAX_BYTES // (1024 * 1024)} MB")
    return data


def private_refs(name: str | None, home: Path | None = None) -> list:
    """[(file name, bytes)] of the private reference set on this machine (at most 3), or [] when it is not there."""
    if not name:
        return []
    folder = (home or Path(os.environ.get("BIE_HOME") or "/var/lib/bie")) / "private" / "refs" / name
    if not folder.is_dir():
        return []
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg"))[:MAX_FRAMES]
    return [(p.name, p.read_bytes()) for p in files if media_of(p.read_bytes()) and p.stat().st_size <= MAX_BYTES]


def apply_overrides(spec: str, names: dict):
    for item in [s for s in (spec or "").split(",") if s]:
        provider, _, value = item.partition("=")
        if provider in names and value:
            os.environ[names[provider]] = value


def run(request: dict, out: Path, *, max_inr: float, gateway: LiveGateway | None = None, opener=None, home: Path | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    rate = usd_inr()
    guard = CostGuard(max_inr, rate=rate)
    ledger = UsageLedger(out / "LEDGER.jsonl")
    if gateway is None:
        routes, missing = build_routes(["google"], max_output_tokens=6000, stream=True)
        if missing:
            raise SystemExit("NOT_CONFIGURED:google")
        gateway = LiveGateway(routes, ledger=ledger, guard=guard)
    else:
        gateway.ledger, gateway.guard = ledger, guard
    refs = private_refs((request.get("reference") or {}).get("private_set"), home)
    references = [(media_of(b), base64.b64encode(b).decode()) for _, b in refs]
    summary = {"schema": "bie.vm-look-run/1", "section": "look", "rule": look.RULE, "rule_version": look.VERSION,
               "reviewer": {"route": "google", "model": gateway.model_of("google")},
               "reference": "frames" if refs else "description",
               "reference_files": [{"name": n, "sha256": hashlib.sha256(b).hexdigest()} for n, b in refs],
               "status": "ok", "error": None, "results": {}}
    for route, urls in request["routes"].items():
        try:
            frames = [fetch(u, opener) for u in urls]
        except (ValueError, OSError) as exc:
            summary["results"][route] = {"error": str(exc)[:300]}
            continue
        msgs = look.messages(request["shot"], route, [(media_of(b), base64.b64encode(b).decode()) for b in frames], references,
                             description=request["reference"]["description"])
        try:
            response = gateway.complete("google", ModelRequest(request_id=f"look:{route}", messages=msgs, response_schema=look.SCHEMA),
                                        prompt_version=f"look-01/{look.VERSION}", check=look.problems, expected_output_tokens=2500)
            summary["results"][route] = dict(response.content, frames=urls)
        except ProviderError as exc:
            summary["results"][route] = {"error": f"{exc.kind}: {str(exc)[-240:]}"}
            if guard.stopped:
                summary.update(status="stopped: budget", error=str(exc)[-240:])
                break
    summary["table"] = look.summary({r: v for r, v in summary["results"].items() if "scores" in v})
    if not summary["table"] and summary["status"] == "ok":
        summary.update(status="failed", error="no route was scored")
    summary["cost"] = {"cap": guard.report(), "total_inr": round(guard.spent_inr, 2), "note": COST_NOTE,
                       "billed_note": "the free Google AI Studio tier bills Rs 0; the guard prices calls at the list price"}
    (out / "look.json").write_text(json.dumps(summary["results"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# LOOK-01 · {request['shot'].get('sentence', '')}", "", f"reference: {summary['reference']}; reviewer "
             f"{summary['reviewer']['model']}; status {summary['status']}", ""]
    for route, value in summary["results"].items():
        if "scores" not in value:
            lines.append(f"- {route}: {value.get('error')}")
            continue
        lines.append(f"## {route} · {value['verdict']} · mean {summary['table'][route]['mean']}")
        lines += [f"- {axis}: {value['scores'][axis]}/10 · {value['reasons'][axis]}" for axis, _ in look.AXES]
        lines += [f"- biggest gap: {value['biggest_gap']}", ""]
    (out / "LOOK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "reference": summary["reference"], "table": summary["table"]}), flush=True)
    return summary


def run_d1(request: dict, out: Path, *, max_inr: float, gateway: LiveGateway | None = None, opener=None) -> dict:
    """LOOK-D1: one reviewer call per part on its still, through the cost guard; the Codex reviewer on the ChatGPT plan (Rs 0)
    unless the request names google (the free tier). Report only (Task 046 Part D1)."""
    out.mkdir(parents=True, exist_ok=True)
    guard = CostGuard(max_inr, rate=usd_inr())
    ledger = UsageLedger(out / "LEDGER.jsonl")
    route = request.get("reviewer", "codex")
    if gateway is None:
        if route == "codex":
            from bie.model_gateway.gpt_adapter import GPTAdapter
            from bie.model_gateway.live.codex_client import DEFAULT_MODEL, CodexExecClient
            routes = {"codex": GPTAdapter(CodexExecClient(), os.environ.get("BIE_CODEX_MODEL") or DEFAULT_MODEL)}
        else:
            routes, missing = build_routes(["google"], max_output_tokens=3000, stream=True)
            if missing:
                raise SystemExit("NOT_CONFIGURED:google")
        gateway = LiveGateway(routes, ledger=ledger, guard=guard)
    else:
        gateway.ledger, gateway.guard = ledger, guard
    summary = {"schema": "bie.vm-look-run/1", "section": "look", "rule": look.D1_RULE, "rule_version": look.D1_VERSION,
               "reviewer": {"route": route, "model": gateway.model_of(route)}, "status": "ok", "error": None, "results": {}}
    for part in request["parts"]:
        try:
            frame = fetch(part["frame"], opener)
        except (ValueError, OSError) as exc:
            summary["results"][part["id"]] = {"error": str(exc)[:300]}
            continue
        msgs = look.d1_messages(part, media_of(frame), base64.b64encode(frame).decode())
        try:
            response = gateway.complete(route, ModelRequest(request_id=f"look-d1:{part['id']}", messages=msgs, response_schema=look.D1_SCHEMA),
                                        prompt_version=f"look-d1/{look.D1_VERSION}", check=look.d1_problems, expected_output_tokens=600)
            summary["results"][part["id"]] = dict(response.content, frame=part["frame"], point=part["point"])
        except ProviderError as exc:
            summary["results"][part["id"]] = {"error": f"{exc.kind}: {str(exc)[-240:]}"}
            if guard.stopped:
                summary.update(status="stopped: budget", error=str(exc)[-240:])
                break
    summary["table"] = look.d1_summary(summary["results"])
    if not summary["table"] and summary["status"] == "ok":
        summary.update(status="failed", error="no part was judged")
    summary["cost"] = {"cap": guard.report(), "total_inr": round(guard.spent_inr, 2), "note": COST_NOTE,
                       "billed_note": "the ChatGPT plan (Codex) and the free Google tier bill Rs 0; the guard prices calls at the list price"}
    (out / "look.json").write_text(json.dumps(summary["results"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# LOOK-D1 · {len(request['parts'])} parts", "", f"reviewer {summary['reviewer']['model']} ({route}); status {summary['status']}; "
             f"{json.dumps(summary['table'], ensure_ascii=False)}", ""]
    for pid, value in summary["results"].items():
        lines.append(f"- {pid}: " + (f"{value['hints_point']}/10{' · TEXT ONLY' if value.get('text_only') else ''} · {value['what_it_shows']}"
                                     + (f" · missing: {value['missing']}" if value.get("missing") else "") if "hints_point" in value else str(value.get("error"))))
    (out / "LOOK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "table": summary["table"]}), flush=True)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--request", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-inr", type=float, default=5.0)
    parser.add_argument("--models", default="")
    parser.add_argument("--routes", default="")
    args = parser.parse_args(argv)
    apply_overrides(args.models, MODEL_ENV)
    apply_overrides(args.routes, VIA_ENV)
    out = Path(args.out)
    from run_brain import read_text
    try:
        request = load_request(read_text(args.request))
    except (ValueError, OSError) as exc:
        out.mkdir(parents=True, exist_ok=True)
        (out / "SUMMARY.json").write_text(json.dumps({"section": "look", "status": "refused", "error": str(exc)[:300]}), encoding="utf-8")
        print(json.dumps({"status": "refused", "error": str(exc)[:300]}))
        return 2
    summary = (run_d1 if request.get("rule") == look.D1_RULE else run)(request, out, max_inr=args.max_inr)
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
