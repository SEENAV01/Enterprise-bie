"""Read and check the toolbox registry and the capability vocabulary (Task 046a).

``load()`` returns a ``Toolbox`` (tools, capabilities) after ``problems()`` finds nothing wrong; every rule of
``registry.schema.json`` is checked here in code, plus the links between the files: a tool may only name known
capabilities, content types, subject families and level profiles, a ``demo_proven`` tool must name its proof, a
``blocked_with_reason`` tool must say why, a share-alike or GPL licence must carry its flag, and the licence flags must
agree with the licence policy (``licence_policy.json``: own terms, per item).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY = HERE / "registry.json"
CAPABILITIES = HERE / "capabilities.json"
SCHEMA = HERE / "registry.schema.json"
LEVELS = HERE.parent / "brain" / "rulebook" / "level_profiles.json"

KINDS = ("python_lib", "js_lib", "asset_source", "dataset", "app")
ROLES = ("compute", "draw", "offline_render", "asset")
PATHS = ("web", "python", "offline")
STATUSES = ("installed", "wrapped", "demo_proven", "used_on_real_book", "blocked_with_reason")
STATUS_RANK = {"used_on_real_book": 4, "demo_proven": 3, "wrapped": 2, "installed": 1, "blocked_with_reason": 0}
FLAGS = ("share_alike", "gpl", "custom", "per_item", "non_commercial")
REQUIRED = ("id", "name", "kind", "subjects", "content_types", "capabilities", "role", "path", "version", "licence",
            "licence_flags", "source", "install_group", "status", "batch", "notes")
OPTIONAL = ("adapter", "block", "levels", "rank", "proof", "blocked_reason")
ID = re.compile(r"^[a-z0-9][a-z0-9_.-]{1,60}$")


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Tool:
    id: str
    name: str
    kind: str
    subjects: tuple
    content_types: tuple
    capabilities: tuple
    role: str
    path: str
    version: str
    licence: str
    licence_flags: tuple
    source: str
    install_group: str
    status: str
    batch: int
    notes: str
    adapter: str = ""
    block: str = ""
    levels: tuple = ()
    rank: int = 50
    proof: dict = field(default_factory=dict)
    blocked_reason: str = ""

    @property
    def usable(self) -> bool:
        return self.status != "blocked_with_reason"


@dataclass(frozen=True)
class Capability:
    id: str
    label: str
    content_types: tuple
    families: tuple
    verbs: tuple
    benchmark_block: str = ""


@dataclass(frozen=True)
class Toolbox:
    version: str
    capabilities_version: str
    npm_before: str
    tools: tuple
    capabilities: dict
    families: tuple
    content_types: tuple

    def tool(self, tool_id: str) -> Tool:
        for t in self.tools:
            if t.id == tool_id:
                return t
        raise KeyError(tool_id)

    def for_capability(self, capability: str) -> list:
        return [t for t in self.tools if capability in t.capabilities]

    def batch(self, number: int) -> list:
        return [t for t in self.tools if t.batch == number]


def _known_levels() -> set:
    try:
        return set(json.loads(LEVELS.read_text(encoding="utf-8"))["profiles"])
    except (OSError, KeyError, ValueError):
        return set()


def _licence_needs(licence: str) -> set:
    """Flags the licence's own name demands, read through the licence policy (``licence_policy.json``); words in
    brackets are notes (history, conditions), not the licence."""
    from . import licence as policy
    kind = policy.normalise(licence)
    needs = {"share-alike": {"share_alike"}, "non-commercial": {"non_commercial"}}.get(kind, set())
    if re.search(policy.policy()["software"]["gpl_pattern"], policy.licence_text(licence)):
        needs = needs | {"gpl"}
    return needs


def problems(registry: dict, capabilities: dict, *, levels: set | None = None, repo_root: Path | None = None) -> list:
    """Everything wrong with the two files, as readable lines (empty when both are fine)."""
    out = []
    levels = _known_levels() if levels is None else levels
    if registry.get("schema") != "bie.toolbox.registry/1":
        out.append("registry: schema must be bie.toolbox.registry/1")
    if capabilities.get("schema") != "bie.toolbox.capabilities/1":
        out.append("capabilities: schema must be bie.toolbox.capabilities/1")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\d+", str(registry.get("version", ""))):
        out.append("registry: version must look like 2026-10-25.1")
    if list(registry.get("statuses") or []) != list(STATUSES):
        out.append("registry: statuses must be " + ", ".join(STATUSES))
    families = set(capabilities.get("families") or [])
    types = set(capabilities.get("content_types") or [])
    caps, seen_caps = {}, set()
    for c in capabilities.get("capabilities") or []:
        cid = c.get("id", "")
        if cid in seen_caps:
            out.append(f"capability {cid}: listed twice")
        seen_caps.add(cid)
        caps[cid] = c
        for t in c.get("content_types") or []:
            if t not in types:
                out.append(f"capability {cid}: unknown content type {t!r}")
        for f in c.get("families") or []:
            if f not in families:
                out.append(f"capability {cid}: unknown family {f!r}")
        if not c.get("verbs"):
            out.append(f"capability {cid}: needs the words that point to it (verbs)")
    seen = set()
    for raw in registry.get("tools") or []:
        tid = raw.get("id", "?")
        where = f"tool {tid}"
        missing = [k for k in REQUIRED if k not in raw]
        if missing:
            out.append(f"{where}: missing {', '.join(missing)}")
            continue
        extra = sorted(set(raw) - set(REQUIRED) - set(OPTIONAL))
        if extra:
            out.append(f"{where}: unknown fields {', '.join(extra)}")
        if not ID.match(tid):
            out.append(f"{where}: id must be lowercase letters, digits, '.', '_' or '-'")
        if tid in seen:
            out.append(f"{where}: listed twice")
        seen.add(tid)
        for key, allowed in (("kind", KINDS), ("role", ROLES), ("path", PATHS), ("status", STATUSES)):
            if raw[key] not in allowed:
                out.append(f"{where}: {key} {raw[key]!r} is not one of {', '.join(allowed)}")
        if not str(raw["source"]).startswith("https://"):
            out.append(f"{where}: source must be an https URL")
        if not str(raw["version"]).strip():
            out.append(f"{where}: version must be pinned")
        if raw["batch"] not in (1, 2, 3):
            out.append(f"{where}: batch must be 1, 2 or 3")
        for s in raw["subjects"]:
            if s not in families:
                out.append(f"{where}: unknown subject family {s!r}")
        for t in raw["content_types"]:
            if t not in types:
                out.append(f"{where}: unknown content type {t!r}")
        for c in raw["capabilities"]:
            if c not in caps:
                out.append(f"{where}: unknown capability {c!r}")
        for flag in raw["licence_flags"]:
            if flag not in FLAGS:
                out.append(f"{where}: unknown licence flag {flag!r}")
        for need in sorted(_licence_needs(raw["licence"]) - set(raw["licence_flags"])):
            out.append(f"{where}: the licence {raw['licence']!r} needs the flag {need}")
        for level in raw.get("levels") or []:
            if levels and level not in levels:
                out.append(f"{where}: unknown level profile {level!r}")
        if raw["status"] == "blocked_with_reason" and not str(raw.get("blocked_reason", "")).strip():
            out.append(f"{where}: blocked_with_reason needs blocked_reason (what it needs)")
        if raw["status"] in ("demo_proven", "used_on_real_book"):
            proof = raw.get("proof") or {}
            if not (proof.get("demos") or proof.get("tests")):
                out.append(f"{where}: status {raw['status']} needs proof (demo ids or test ids)")
        for test in (raw.get("proof") or {}).get("tests", []) if repo_root is not None else []:
            file, _, name = str(test).split(" ")[0].partition("::")      # "tests/x.py::Class" or "tools/toolbox_demos.py --bridge <demo>"
            text = Path(repo_root, file).read_text(encoding="utf-8") if Path(repo_root, file).is_file() else ""
            if not text or (name and f"class {name}(" not in text):
                out.append(f"{where}: proof test {test!r} does not exist")
        if raw.get("adapter") and repo_root is not None:
            module = Path(repo_root, *raw["adapter"].split(".")).with_suffix(".py")
            if not module.exists():
                out.append(f"{where}: adapter {raw['adapter']} does not exist")
    from . import licence as policy
    out += policy.registry_problems(registry.get("tools") or [])
    return out


def _tool(raw: dict) -> Tool:
    return Tool(id=raw["id"], name=raw["name"], kind=raw["kind"], subjects=tuple(raw["subjects"]),
                content_types=tuple(raw["content_types"]), capabilities=tuple(raw["capabilities"]), role=raw["role"],
                path=raw["path"], version=str(raw["version"]), licence=raw["licence"], licence_flags=tuple(raw["licence_flags"]),
                source=raw["source"], install_group=raw["install_group"], status=raw["status"], batch=int(raw["batch"]),
                notes=raw["notes"], adapter=raw.get("adapter", ""), block=raw.get("block", ""), levels=tuple(raw.get("levels") or ()),
                rank=int(raw.get("rank", 50)), proof=dict(raw.get("proof") or {}), blocked_reason=raw.get("blocked_reason", ""))


def from_data(registry: dict, capabilities: dict, *, check: bool = True, repo_root: Path | None = None) -> Toolbox:
    if check:
        found = problems(registry, capabilities, repo_root=repo_root)
        if found:
            raise RegistryError("; ".join(found[:12]))
    caps = {c["id"]: Capability(id=c["id"], label=c["label"], content_types=tuple(c["content_types"]),
                                families=tuple(c["families"]), verbs=tuple(c["verbs"]), benchmark_block=c.get("benchmark_block", ""))
            for c in capabilities["capabilities"]}
    return Toolbox(version=registry["version"], capabilities_version=capabilities["version"], npm_before=registry["npm_before"],
                   tools=tuple(_tool(t) for t in registry["tools"]), capabilities=caps,
                   families=tuple(capabilities["families"]), content_types=tuple(capabilities["content_types"]))


@lru_cache(maxsize=1)
def load() -> Toolbox:
    return from_data(json.loads(REGISTRY.read_text(encoding="utf-8")), json.loads(CAPABILITIES.read_text(encoding="utf-8")),
                     repo_root=HERE.parents[1])
