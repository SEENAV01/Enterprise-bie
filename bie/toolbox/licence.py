"""BIE's licence policy and the lesson licence gate (Task 046a-L).

Navin, 25 October 2026: "Final videos mein sirf CC0 aur CC BY assets lein; CC BY-SA nahi; NC bilkul nahi."

``licence_policy.json`` next to this file is the only source of truth; every licence decision in BIE reads it through
this module (standard library only, so every lane can import it):

- ``classify(licence)``: the policy class of a licence text (public-domain, cc-by, share-alike, non-commercial ...) and
  its lesson verdict: allowed, refused or needs_navin. Words in brackets are notes (history, conditions), not the licence.
- ``asset_verdict(asset)``: the verdict for one file (an ``Asset`` or ``Candidate`` of ``bie.brain.assets``, a dict, an
  old-path asset record): its source (needs Navin by name, per item, BIE's own), India's boundary, its licence class,
  and for CC BY the four credit fields (author, licence, licence URL, source page).
- ``lesson_licence_check(assets)``: the gate. A list of problems, empty when every asset may appear in a lesson.
  ``require_lesson_assets`` raises ``LicenceError`` with them; this is the hook the Task 046 director calls before it
  renders or packages a lesson. ``lesson_spec_check(spec)`` stops a video spec that draws India's boundary.
- ``lesson_credits(assets)``: one credit line per outside asset, built from the asset's own fields.
- ``tool_verdict(tool)``: a registry tool's lesson-use verdict: software (the program's licence governs the program,
  not what BIE draws with it), or content (allowed, refused, needs Navin, per item).

Nothing here swaps a refused asset for another one: the caller stops that output and says why.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
POLICY = HERE / "licence_policy.json"
VERDICTS = ("allowed", "refused", "needs_navin", "per_item")
VERDICT_TEXT = {"allowed": "allowed", "refused": "refused", "needs_navin": "needs Navin", "per_item": "per item"}
CONTENT_KINDS = ("asset_source", "dataset")
INTERNAL_PROOF = "internal proof, not for lessons"


class LicenceError(ValueError):
    """A lesson output was stopped by the licence gate; ``problems`` says which asset and why."""

    def __init__(self, problems, where: str = ""):
        self.problems = list(problems)
        super().__init__((f"{where}: " if where else "") + "; ".join(self.problems[:8]))


@dataclass(frozen=True)
class Verdict:
    verdict: str                  # allowed | refused | needs_navin | per_item
    reason: str
    licence_class: str = ""
    credit_required: bool = False
    basis: str = "content"        # content | software | own
    note: str = ""                # a condition that does not change the verdict (India's boundary, an open decision)

    @property
    def allowed(self) -> bool:
        return self.verdict == "allowed"

    @property
    def text(self) -> str:
        return VERDICT_TEXT[self.verdict]


# ---------------------------------------------------------------- the policy file

def policy_problems(data: dict) -> list:
    """Everything wrong with the policy file, as readable lines (empty when it is fine)."""
    out = []
    if data.get("schema") != "bie.toolbox.licence-policy/1":
        out.append("policy: schema must be bie.toolbox.licence-policy/1")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\d+", str(data.get("version", ""))):
        out.append("policy: version must look like 2026-10-25.1")
    decided = data.get("decided") or {}
    if not (decided.get("date") and decided.get("by") and decided.get("words")):
        out.append("policy: decided needs date, by and Navin's words")
    seen = set()
    for c in data.get("classes") or []:
        cid = c.get("id", "?")
        if cid in seen:
            out.append(f"class {cid}: listed twice")
        seen.add(cid)
        if c.get("verdict") not in ("allowed", "refused", "needs_navin"):
            out.append(f"class {cid}: verdict must be allowed, refused or needs_navin")
        if not c.get("match") or not c.get("reason"):
            out.append(f"class {cid}: needs match patterns and a reason")
        for pattern in c.get("match") or []:
            try:
                re.compile(pattern)
            except re.error as exc:
                out.append(f"class {cid}: pattern {pattern!r} does not compile ({exc})")
    for need in ("public-domain", "cc-by", "share-alike", "non-commercial", "no-derivatives", "own-terms"):
        if need not in seen:
            out.append(f"policy: class {need} is missing")
    allowed = {c["id"] for c in data.get("classes") or [] if c.get("verdict") == "allowed"}
    if not allowed <= {"public-domain", "cc-by", "font", "own-work"}:
        out.append(f"policy: only CC0/public domain, CC BY, fonts and BIE's own work may be allowed, not {sorted(allowed)}")
    if (data.get("unreadable") or {}).get("verdict") != "refused":
        out.append("policy: a missing or unreadable licence must be refused")
    if set(data.get("credit_fields") or []) != {"author", "licence", "licence_url", "page_url"}:
        out.append("policy: credit_fields must be author, licence, licence_url, page_url")
    sources = data.get("sources") or {}
    ids = []
    for group in ("needs_navin", "per_item"):
        for s in sources.get(group) or []:
            ids.append(s.get("id"))
            if not s.get("asset_sources"):
                out.append(f"source {s.get('id')}: needs asset_sources")
            if group == "needs_navin" and not s.get("why"):
                out.append(f"source {s.get('id')}: needs a reason (why)")
    if len(ids) != len(set(ids)):
        out.append("policy: a source is listed twice")
    for approved in sources.get("approved_by_navin") or []:
        if not (isinstance(approved, dict) and approved.get("id") and approved.get("approved_on") and approved.get("words")):
            out.append("policy: an approved source needs id, approved_on and Navin's words")
    generated = data.get("generated_images")
    if generated is not None:
        if not generated.get("asset_sources") or not generated.get("provenance_fields") or not (generated.get("decided") or {}).get("words"):
            out.append("policy: generated_images needs asset_sources, provenance_fields and Navin's words (decided)")
        if generated.get("verdict") != "allowed":
            out.append("policy: generated_images verdict must be allowed (with the provenance) or the block removed")
    boundary = data.get("india_boundary") or {}
    if boundary.get("verdict") != "needs_navin" and not boundary.get("approved_boundary"):
        out.append("policy: India's boundary stays needs_navin until Navin approves a boundary")
    if not boundary.get("tag") or not boundary.get("blocks"):
        out.append("policy: india_boundary needs its tag and the blocks that draw it")
    return out


@lru_cache(maxsize=1)
def policy() -> dict:
    data = json.loads(POLICY.read_text(encoding="utf-8"))
    found = policy_problems(data)
    if found:
        raise LicenceError(found, "licence_policy.json")
    return data


@lru_cache(maxsize=1)
def _classes() -> tuple:
    return tuple((c, tuple(re.compile(p) for p in c["match"])) for c in policy()["classes"])


def version() -> str:
    return policy()["version"]


# ---------------------------------------------------------------- licences

def licence_text(licence: str) -> str:
    """The licence's own words, lower case: bracketed notes are dropped (unless nothing else is left)."""
    raw = re.sub(r"\s+", " ", str(licence or "")).strip()
    main = re.sub(r"\([^)]*\)", " ", raw)
    main = re.sub(r"\s+", " ", main).strip(" ;,.")
    return (main or raw).lower()


def classify(licence: str) -> Verdict:
    text = licence_text(licence)
    if text:
        for cls, patterns in _classes():
            if any(p.search(text) for p in patterns):
                return Verdict(cls["verdict"], cls["reason"], cls["id"], bool(cls.get("credit_required")),
                               "own" if cls["id"] == "own-work" else "content")
    rule = policy()["unreadable"]
    return Verdict(rule["verdict"], rule["reason"], "unknown")


def normalise(licence: str) -> str:
    """The policy class id of a licence (public-domain, cc-by, share-alike, non-commercial, no-derivatives, ...)."""
    return classify(licence).licence_class


def allowed(licence: str) -> bool:
    """True when the licence alone allows lesson use (sources and credit fields are checked by ``asset_verdict``)."""
    return classify(licence).allowed


def never_fetched(licence: str) -> bool:
    """Licences BIE does not even download (not for lessons, not for internal proofs)."""
    return normalise(licence) in (policy().get("never_fetched") or {}).get("classes", [])


# ---------------------------------------------------------------- sources

def _source_entries() -> dict:
    """asset source name or registry id → (group, entry)."""
    srcs = policy()["sources"]
    out = {}
    approved = {a["id"] for a in srcs.get("approved_by_navin") or []}
    for group in ("needs_navin", "per_item"):
        for entry in srcs.get(group) or []:
            kind = "approved" if group == "needs_navin" and entry["id"] in approved else group
            for name in [entry["id"], *entry.get("asset_sources", [])]:
                out[name] = (kind, entry)
    return out


def source_id(source: str) -> str:
    """The registry id behind an asset's ``source`` (``z_anatomy`` → ``z-anatomy``; policy aliases for the rest)."""
    name = str(source or "").strip()
    aliases = policy()["sources"].get("aliases") or {}
    if name in aliases:
        return aliases[name]
    entry = _source_entries().get(name)
    return entry[1]["id"] if entry else name.replace("_", "-")


def source_rule(source: str):
    """("needs_navin" | "approved" | "per_item" | "own" | "", entry) for an asset source or registry id."""
    name = str(source or "").strip()
    if name in policy()["own_work"]["asset_sources"]:
        return "own", policy()["own_work"]
    generated = policy().get("generated_images") or {}
    if name in (generated.get("asset_sources") or []):
        return "generated", generated
    entries = _source_entries()
    return entries.get(name) or entries.get(source_id(name), ("", {}))


# ---------------------------------------------------------------- assets

def _get(asset, key: str, default=""):
    if isinstance(asset, dict):
        return asset.get(key, default)
    return getattr(asset, key, default)


def _approval(source: str) -> str:
    entry = next(a for a in policy()["sources"].get("approved_by_navin") or [] if a["id"] == source)
    return f"{source}: approved by Navin on {entry['approved_on']}: {entry['words']}"


def _asset_name(asset) -> str:
    ident = _get(asset, "asset_id") or _get(asset, "id")
    title = _get(asset, "title")
    return f"{ident} ({title})" if ident and title else str(ident or title or "asset")


def asset_verdict(asset, *, check_credit: bool = True) -> Verdict:
    """The lesson verdict for one file. ``check_credit=False`` only for records that never kept the credit fields
    (old demo receipts); a lesson always checks them."""
    pol = policy()
    tags = {str(t).lower() for t in (_get(asset, "tags", None) or [])}
    boundary = pol["india_boundary"]
    if boundary["tag"] in tags and not boundary.get("approved_boundary"):
        return Verdict("needs_navin", boundary["why"], "india-boundary")
    kind, entry = source_rule(_get(asset, "source"))
    if kind == "own":
        return Verdict("allowed", entry["reason"], "own-work", False, "own")
    if kind == "generated":                      # Route 2 (Navin, 29 October 2026): BIE's own image, with its provenance on the asset
        missing = [f for f in entry["provenance_fields"] if not str(_get(asset, f) or "").strip()]
        if missing:
            return Verdict("refused", f"a generated image needs its provenance on the asset; missing: {', '.join(missing)}", "generated", False, "own")
        return Verdict("allowed", entry["reason"] + f" (Navin, {entry['decided']['date']})", "generated", False, "own")
    if kind == "needs_navin":
        return Verdict("needs_navin", f"{entry['id']}: {entry['why']}", "own-terms")
    if kind == "approved":                       # Navin approved this source by name: its own terms, with a full credit
        missing = [f for f in pol["credit_fields"] if not str(_get(asset, f) or "").strip()] if check_credit else []
        if missing:
            return Verdict("refused", f"{entry['id']} (approved by Navin) needs a credit; missing: {', '.join(missing)}", "approved", True)
        return Verdict("allowed", _approval(entry["id"]), "approved", True)
    if _get(asset, "third_party", False):
        third = next(c for c in pol["classes"] if c["id"] == "third-party")
        return Verdict("refused", third["reason"], "third-party")
    verdict = classify(_get(asset, "licence"))
    if not verdict.allowed or not (check_credit and verdict.credit_required):
        return verdict
    missing = [f for f in pol["credit_fields"] if not str(_get(asset, f) or "").strip()]
    if missing:
        name = {"cc-by": "CC BY"}.get(verdict.licence_class, verdict.licence_class)
        return Verdict("refused", f"{name} needs a credit; missing: {', '.join(missing)}",
                       verdict.licence_class, True)
    return verdict


def lesson_licence_check(assets, *, check_credit: bool = True) -> list:
    """The gate: one line per asset that may not appear in a lesson (empty list: every asset may)."""
    problems = []
    for asset in assets:
        v = asset_verdict(asset, check_credit=check_credit)
        if not v.allowed:
            problems.append(f"{_asset_name(asset)}: {v.text}: {v.reason}")
    return problems


def require_lesson_assets(assets, *, where: str = "lesson") -> list:
    """The hook for every lesson output (Task 046 director, visual section, Scene IR, compiler): raises
    ``LicenceError`` when any asset is refused or waits for Navin; returns the credits when all may be used."""
    assets = list(assets)
    problems = lesson_licence_check(assets)
    if problems:
        raise LicenceError(problems, where)
    return lesson_credits(assets)


def credit_line(asset) -> str:
    v = classify(_get(asset, "licence"))
    licence = str(_get(asset, "licence") or "").strip()
    url = str(_get(asset, "licence_url") or "").strip()
    parts = [str(_get(asset, "title") or "").strip() or _asset_name(asset),
             str(_get(asset, "author") or "").strip() or "author not named",
             f"{licence} ({url})" if url and v.licence_class == "cc-by" else licence,
             str(_get(asset, "page_url") or "").strip()]
    return " · ".join(p for p in parts if p)


def lesson_credits(assets) -> list:
    """Credit lines for the outside assets of a lesson (BIE's own work needs none), in the order given, once each."""
    lines, seen = [], set()
    for asset in assets:
        if source_rule(_get(asset, "source"))[0] == "own" or classify(_get(asset, "licence")).basis == "own":
            continue
        line = credit_line(asset)
        if line not in seen:
            seen.add(line)
            lines.append(line)
    return lines


def lesson_spec_check(spec: dict) -> list:
    """Problems in a lesson video spec itself: a block that draws India's political boundary waits for Navin."""
    boundary = policy()["india_boundary"]
    if boundary.get("approved_boundary"):
        return []
    problems = []
    for scene in (spec or {}).get("scenes") or []:
        for layer in scene.get("layers") or []:
            if layer.get("type") == "block" and layer.get("block") in boundary["blocks"]:
                problems.append(f"scene {scene.get('id', '?')} block {layer.get('block')}: needs Navin: {boundary['why']}")
    return problems


def record_items(licence) -> tuple:
    """A licence record kept on a frozen old-path record: a dict becomes sorted (key, value) pairs (tags as a tuple)."""
    if not licence:
        return ()
    items = dict(licence)
    if not all(isinstance(k, str) for k in items):
        raise ValueError("licence record keys must be text")
    return tuple(sorted((k, tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in items.items()))


def from_record(asset_id: str, rights_basis: str, licence=None, *, title: str = "") -> dict:
    """An old-path asset record (Scene IR ``AssetRecord``, compiler ``CompilerAssetRecord``) as an asset the gate reads:
    its structured ``licence`` mapping when it has one, otherwise its rights basis read as the licence."""
    asset = {"asset_id": asset_id, "title": title, "licence": rights_basis, "source": "", "tags": []}
    if licence:
        asset.update(dict(licence))
        asset["asset_id"] = asset_id
    return asset


# ---------------------------------------------------------------- tools (registry)

def is_content(tool) -> bool:
    return _get(tool, "kind") in CONTENT_KINDS or _get(tool, "role") == "asset"


def tool_verdict(tool) -> Verdict:
    """A registry tool's lesson-use verdict, derived from the policy (never written by hand per tool)."""
    pol = policy()
    tid, licence = _get(tool, "id"), _get(tool, "licence")
    flags = set(_get(tool, "licence_flags", None) or ())
    if not is_content(tool):
        decisions = {d["id"]: d["decision"] for d in pol["software"].get("open_decisions") or []}
        decisions.update({d["id"]: f"decided by Navin on {d['decided_on']}: {d['decision']}" for d in pol["software"].get("decided") or []})
        copyleft = "gpl" in flags or re.search(pol["software"]["copyleft_pattern"], str(licence).lower())
        note = "; ".join(n for n in (pol["software"]["gpl"] if copyleft else "", decisions.get(tid, "")) if n)
        return Verdict("allowed", pol["software"]["rule"], "software", False, "software", note)
    boundary = pol["india_boundary"]
    note = boundary["why"] if tid in boundary["sources"] and not boundary.get("approved_boundary") else ""
    kind, entry = source_rule(tid)
    if kind == "own":
        return Verdict("allowed", entry["reason"], "own-work", False, "own")
    if kind == "approved":
        return Verdict("allowed", _approval(tid), "approved", True, note=note)
    if kind == "per_item" or "per_item" in flags:
        return Verdict("per_item", entry.get("rule") or "each file is checked on its own licence", "per-item", note=note)
    if kind == "needs_navin":
        return Verdict("needs_navin", entry["why"], "own-terms", note=note)
    verdict = classify(licence)
    if "custom" in flags and kind != "approved" and verdict.verdict != "refused":
        return Verdict("needs_navin", f"own licence: {licence}", "own-terms", note=note)
    return Verdict(verdict.verdict, verdict.reason, verdict.licence_class, verdict.credit_required, verdict.basis, note)


def registry_problems(tools) -> list:
    """The registry and the policy must agree: a content tool with its own licence (custom flag) is named in the policy
    (needs Navin or approved), a per-item content tool is in the policy's per-item list, and the reverse."""
    out = []
    entries = _source_entries()
    for raw in tools:
        tid = _get(raw, "id")
        flags = set(_get(raw, "licence_flags", None) or ())
        if not is_content(raw):
            continue
        kind = entries.get(tid, ("", {}))[0]
        if "custom" in flags and kind not in ("needs_navin", "approved"):
            out.append(f"tool {tid}: own licence (custom) but not named in licence_policy.json (needs_navin or approved_by_navin)")
        if kind in ("needs_navin", "approved") and "custom" not in flags:
            out.append(f"tool {tid}: licence_policy.json names it as own terms; the registry needs the custom flag")
        if ("per_item" in flags) != (kind == "per_item"):
            out.append(f"tool {tid}: per_item flag and licence_policy.json's per-item list disagree")
        if classify(_get(raw, "licence")).licence_class == "own-terms" and "custom" not in flags:
            out.append(f"tool {tid}: the licence {_get(raw, 'licence')!r} is own terms; it needs the custom flag")
    return out


def program_names(tool) -> set:
    """Names under which a program can appear in a dependency manifest or an import: its registry id, its Python
    module and distribution, its npm package, and the policy's extra names (Blender's ``bpy``)."""
    tid = _get(tool, "id")
    names = {tid}
    names.update(policy()["software"].get("extra_names", {}).get(tid, []))
    try:
        from .adapters.base import PYTHON_TOOLS
        if tid in PYTHON_TOOLS:
            module, dist = PYTHON_TOOLS[tid][:2]
            names.update((module, module.split(".")[0], dist))
    except ImportError:
        pass
    web = json.loads((HERE / "web_packages.json").read_text(encoding="utf-8")).get("tool_packages", {})
    if tid in web:
        names.add(web[tid])
    return {n for n in names if n}


def copyleft_programs(tools) -> list:
    """Software tools whose licence is GPL or LGPL (flag or name): cloud, CI or VM only, never inside apps/."""
    pattern = policy()["software"]["copyleft_pattern"]
    return [t for t in tools if not is_content(t) and ("gpl" in set(_get(t, "licence_flags", None) or ())
                                                        or re.search(pattern, str(_get(t, "licence")).lower()))]


SKIP_DIRS = {"node_modules", "build", ".gradle", "dist", "__pycache__", ".venv", "venv"}


def apps_copyleft_problems(apps_root, tools) -> list:
    """One line for every GPL or LGPL program (``copyleft_programs``) that a dependency manifest under ``apps_root``
    names, or that app code imports: such programs run only in the cloud, CI or VM render path, never inside apps/."""
    root = Path(apps_root)
    software = policy()["software"]
    names = {t.id if hasattr(t, "id") else t["id"]: program_names(t) for t in copyleft_programs(tools)}

    def files(patterns):
        found = set()
        for pattern in patterns:
            found |= {p for p in root.glob(pattern) if p.is_file() and not SKIP_DIRS & set(p.relative_to(root).parts)}
        return sorted(found)

    out = []
    for path in files(software["apps_manifests"]):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for tid, words in sorted(names.items()):
            hit = next((w for w in sorted(words) if re.search(r"(?<![a-z0-9_.@/-])" + re.escape(w.lower()) + r"(?![a-z0-9_-])", text)), None)
            if hit:
                out.append(f"{path.relative_to(root.parent).as_posix()}: names {hit!r} ({tid}, a GPL-family program): "
                           "copyleft programs stay in the cloud, CI or VM render path")
    for path in files(software["apps_code"]):
        text = path.read_text(encoding="utf-8", errors="replace")
        for tid, words in sorted(names.items()):
            for w in sorted(words):
                py = re.search(r"^\s*(?:import|from)\s+" + re.escape(w) + r"(?:[.\s,]|$)", text, re.M) if path.suffix == ".py" else None
                js = re.search(r"""(?:from\s+|require\(\s*|import\s*\(?\s*)['"]""" + re.escape(w) + r"""(?:/[^'"]*)?['"]""", text) \
                    if path.suffix in (".js", ".mjs", ".ts", ".tsx") else None
                if py or js:
                    out.append(f"{path.relative_to(root.parent).as_posix()}: imports {w!r} ({tid}, a GPL-family program): "
                               "copyleft programs stay in the cloud, CI or VM render path")
                    break
    return out
