"""Lossless archive inspection and explicit canonical path resolution."""
from __future__ import annotations

import ast
import hashlib
import io
from pathlib import PurePosixPath
import re
import stat
import zipfile

ROOT_MAP = {"enterprise": "infrastructure", "book_intelligence": "document_intelligence", "game_ir": "game_engine"}
TERMINAL_STATES = frozenset({"MIGRATED", "ARCHIVED_EVIDENCE", "DUPLICATE_WITH_PROVENANCE", "EXCLUDED_WITH_REASON"})


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(name: str) -> str:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name or "\x00" in name:
        raise ValueError(f"Unsafe archive path: {name!r}")
    if p.as_posix() != name.rstrip("/") or any(x in {".git", ".hg", ".svn"} for x in p.parts):
        raise ValueError(f"Noncanonical archive path: {name!r}")
    return p.as_posix()


def inspect_zip(data: bytes, expected_sha: str | None = None, max_bytes: int = 128 * 1024 * 1024) -> dict[str, bytes]:
    """Validate all members before the caller writes anything; never execute imports."""
    if expected_sha is not None and digest(data) != expected_sha:
        raise ValueError("Archive checksum mismatch")
    result, seen, total = {}, set(), 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos = z.infolist()
        if len(infos) > 50000:
            raise ValueError("Archive member limit exceeded")
        for info in infos:
            name = safe_path(info.filename)
            folded = name.casefold()
            if folded in seen:
                raise ValueError(f"Duplicate/case-colliding member: {name}")
            seen.add(folded)
            mode = info.external_attr >> 16
            if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError(f"Nonregular archive member: {name}")
            if info.flag_bits & 1:
                raise ValueError("Encrypted archive requires separate recovery")
            total += info.file_size
            if total > max_bytes or info.file_size > max_bytes or info.file_size > max(1, info.compress_size) * 10000:
                raise ValueError("Archive expansion limit exceeded")
            if not info.is_dir():
                result[name] = z.read(info)
        names = set(result)
        if any(str(parent) in names for name in names for parent in PurePosixPath(name).parents):
            raise ValueError("File/directory collision")
    return result


def canonical_source(path: str) -> str | None:
    if not path.startswith("app/bie/"):
        return None
    pieces = path.split("/")[2:]
    pieces[0] = ROOT_MAP.get(pieces[0], pieces[0])
    return "/".join(["bie", *pieces])


def resolve_version(versions: list[dict], selected_sha: str | None = None) -> dict:
    """An unresolved differing-content collision never chooses a lexical/latest winner."""
    if not versions:
        raise ValueError("No source versions")
    hashes = {x["sha256"] for x in versions}
    if len(hashes) > 1 and selected_sha not in hashes:
        return {"status": "CONFLICT", "versions": versions}
    winner = next(x for x in versions if x["sha256"] == (selected_sha or versions[0]["sha256"]))
    return {"status": "RESOLVED", "selected": winner, "versions": versions}


def normalize_imports(text: str, roots: set[str], bare_modules: dict[str, str]) -> str:
    """Rewrite only import statements; preserve source formatting and literal contents."""
    lines = text.splitlines(keepends=True)
    edits = []
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, ast.ImportFrom) or node.level or not node.module:
            continue
        old = node.module
        bits = old.split(".")
        if bits[:2] == ["app", "bie"]:
            bits = bits[2:]
        elif bits[0] not in roots:
            if old not in bare_modules:
                continue
            bits = bare_modules[old].split(".")[1:]
        bits[0] = ROOT_MAP.get(bits[0], bits[0])
        new = ".".join(["bie", *bits])
        if old == new:
            continue
        index = node.lineno - 1
        line = lines[index]
        # All recovered imports are single-line 'from ... import ...' statements.
        prefix, suffix = line[:node.col_offset], line[node.col_offset:]
        replacement, count = re.subn(r"^(from\s+)" + re.escape(old) + r"(\s+import\b)", lambda m: m[1] + new + m[2], suffix, count=1)
        if count != 1:
            raise ValueError(f"Import needs explicit migration: {old}")
        edits.append((index, prefix + replacement))
    for index, value in edits:
        lines[index] = value
    result = "".join(lines)
    ast.parse(result)
    return result
