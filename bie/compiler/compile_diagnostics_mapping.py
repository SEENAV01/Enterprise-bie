"""QA-001: content-bound generated TS/TSX -> Scene IR diagnostic provenance.

This is a generated-source origin map, not a JavaScript/VLQ source map. It preserves
source-reference IDs; it never fabricates book page numbers or text offsets.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import re
from .compiler_diagnostics import CompilerDiagnostic
from .qa_common import CompilerQAError, digest, positive_int, source_files, token
from .artifact_hashing import safe_relative, require_sha256

@dataclass(frozen=True)
class SourceOrigin:
    scene_id: str
    scene_path: str
    element_id: str | None
    track_id: str | None
    source_refs: tuple[str, ...]
    reasoning_refs: tuple[str, ...]
    owner: str = "COMP"
    def __post_init__(self) -> None:
        for name in ("scene_id", "scene_path", "owner"):
            token(getattr(self, name), name)
        for name in ("element_id", "track_id"):
            if getattr(self, name) is not None:
                token(getattr(self, name), name)
        for name in ("source_refs", "reasoning_refs"):
            values = tuple(getattr(self, name))
            if not values or len(values) != len(set(values)):
                raise CompilerQAError("missing/duplicate provenance refs")
            for value in values:
                token(value, name)
            object.__setattr__(self, name, values)

@dataclass(frozen=True)
class GeneratedSourceSpan:
    path: str
    start_line: int
    end_line: int
    source_sha256: str
    origin: SourceOrigin
    def __post_init__(self) -> None:
        safe_relative(self.path)
        positive_int(self.start_line, "start_line")
        positive_int(self.end_line, "end_line")
        if self.end_line < self.start_line:
            raise CompilerQAError("reversed source span")
        require_sha256(self.source_sha256)
        if not isinstance(self.origin, SourceOrigin):
            raise CompilerQAError("typed SourceOrigin required")

@dataclass(frozen=True)
class GeneratedSourceMap:
    scene_fingerprint: str
    spans: tuple[GeneratedSourceSpan, ...]
    source_identity: tuple[tuple[str, str], ...]
    map_sha256: str
    accepted: bool = False


def build_source_map(*, scene_fingerprint: str, files: Iterable,
                     spans: Iterable[GeneratedSourceSpan]) -> GeneratedSourceMap:
    require_sha256(scene_fingerprint)
    contents = {p: (c, h) for p, c, h in source_files(files)}
    ordered = tuple(sorted(spans, key=lambda s: (s.path, s.start_line, s.end_line)))
    last: dict[str, int] = {}
    for span in ordered:
        if span.path not in contents:
            raise CompilerQAError("source span refers to missing generated file")
        content, actual = contents[span.path]
        if actual != span.source_sha256:
            raise CompilerQAError("stale source map content hash")
        if span.end_line > max(1, len(content.splitlines())):
            raise CompilerQAError("source span exceeds generated file")
        if span.start_line <= last.get(span.path, 0):
            raise CompilerQAError("ambiguous overlapping source spans")
        last[span.path] = span.end_line
    identity = tuple(sorted((p, h) for p, (_, h) in contents.items()))
    payload = {"scene_fingerprint": scene_fingerprint,
               "spans": [asdict(s) for s in ordered], "source_identity": identity}
    return GeneratedSourceMap(scene_fingerprint, ordered, identity, digest(payload))


def source_map_from_dict(raw: dict) -> GeneratedSourceMap:
    try:
        if raw.get("accepted") is not False:
            raise CompilerQAError("source map cannot claim acceptance")
        spans = []
        for item in raw["spans"]:
            item = dict(item)
            origin = dict(item.pop("origin"))
            origin["source_refs"] = tuple(origin["source_refs"])
            origin["reasoning_refs"] = tuple(origin["reasoning_refs"])
            spans.append(GeneratedSourceSpan(origin=SourceOrigin(**origin), **item))
        return GeneratedSourceMap(raw["scene_fingerprint"], tuple(spans),
                                  tuple(tuple(x) for x in raw["source_identity"]), raw["map_sha256"])
    except (KeyError, TypeError) as exc:
        raise CompilerQAError("invalid source map document") from exc


def validate_source_map(mapping: GeneratedSourceMap, files: Iterable) -> None:
    actual = build_source_map(scene_fingerprint=mapping.scene_fingerprint,
                              files=files, spans=mapping.spans)
    if mapping != actual:
        raise CompilerQAError("source map/manifest integrity mismatch")

@dataclass(frozen=True)
class RawCompileDiagnostic:
    code: str
    severity: str
    stage: str
    message: str
    file: str = ""
    line: int | None = None
    column: int | None = None
    def __post_init__(self) -> None:
        for name in ("code", "stage", "message"):
            token(getattr(self, name), name)
        if self.severity not in {"ERROR", "WARNING", "INFO"}:
            raise CompilerQAError("invalid diagnostic severity")
        if not isinstance(self.file, str):
            raise CompilerQAError("invalid diagnostic filename")
        for name in ("line", "column"):
            if getattr(self, name) is not None:
                positive_int(getattr(self, name), name)
        if self.column is not None and self.line is None:
            raise CompilerQAError("column requires line")

@dataclass(frozen=True)
class MappedCompileDiagnostic:
    diagnostic_id: str
    code: str
    severity: str
    stage: str
    message: str
    file: str
    line: int | None
    column: int | None
    origin: SourceOrigin | None
    mapping_status: str

@dataclass(frozen=True)
class CompileDiagnosticsReceipt:
    diagnostics: tuple[MappedCompileDiagnostic, ...]
    error_count: int
    warning_count: int
    unmapped_count: int
    source_map_sha256: str
    passed: bool
    accepted: bool = False

_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_TSC = re.compile(r"^(?:(.*?)\((\d+),(\d+)\):\s*)?(error|warning)\s+(TS\d+):\s*(.*)$")
_TSC_COLON = re.compile(r"^(.*?):(\d+):(\d+)\s*[-:]\s*(error|warning)\s+(TS\d+):\s*(.*)$")


def parse_compile_output(text: str, *, stage: str = "typescript") -> tuple[RawCompileDiagnostic, ...]:
    """Consume --pretty false TypeScript diagnostics, including continuation lines."""
    if not isinstance(text, str):
        raise CompilerQAError("compile output must be text")
    parsed: list[RawCompileDiagnostic] = []
    current: dict | None = None
    for line in _ANSI.sub("", text).splitlines():
        match = _TSC.match(line.strip()) or _TSC_COLON.match(line.strip())
        if match:
            if current:
                parsed.append(RawCompileDiagnostic(**current))
            file, lineno, col, severity, code, message = match.groups()
            current = dict(code=code, severity=severity.upper(), stage=stage,
                           message=message or code, file=file or "",
                           line=int(lineno) if lineno else None, column=int(col) if col else None)
        elif current and line[:1].isspace() and line.strip():
            # JSON-escaped newline keeps the diagnostic message usable by strict contracts.
            current["message"] += " | " + line.strip()
        elif line.strip():
            if current:
                parsed.append(RawCompileDiagnostic(**current)); current = None
    if current:
        parsed.append(RawCompileDiagnostic(**current))
    return tuple(parsed)


def _relative_diagnostic_path(path: str, workspace: str | Path | None) -> str | None:
    if not path:
        return ""
    normalized = path.replace("\\", "/")
    # Preserve lexical Windows origins without pretending they are POSIX roots.
    if re.match(r"^[A-Za-z]:/", normalized):
        if workspace is None:
            return None
        base = str(workspace).replace("\\", "/").rstrip("/") + "/"
        if not normalized.startswith(base):
            return None
        normalized = normalized[len(base):]
    elif normalized.startswith("/"):
        if workspace is None:
            return None
        try:
            normalized = Path(normalized).relative_to(Path(workspace).absolute()).as_posix()
        except ValueError:
            return None
    if normalized.startswith("./"):
        normalized = normalized[2:]
    try:
        return safe_relative(normalized)
    except ValueError:
        return None


def map_compile_diagnostics(diagnostics: Iterable[RawCompileDiagnostic], *,
                            source_map: GeneratedSourceMap, files: Iterable,
                            workspace: str | Path | None = None,
                            process_exit_code: int = 0) -> CompileDiagnosticsReceipt:
    if type(process_exit_code) is not int:
        raise CompilerQAError("process exit code must be an integer")
    files = tuple(files)
    validate_source_map(source_map, files)
    items = list(diagnostics)
    if process_exit_code and not any(d.severity == "ERROR" for d in items):
        items.append(RawCompileDiagnostic("COMP_PROCESS_FAILURE", "ERROR", "build",
                     f"Compiler process exited {process_exit_code} without a parsed error."))
    unique = {}
    for item in items:
        path = _relative_diagnostic_path(item.file, workspace)
        origin = None
        status = "GLOBAL" if not item.file else "UNMAPPED"
        if path is None:
            status = "OUTSIDE_WORKSPACE"
        elif path and item.line is not None:
            candidates = [s for s in source_map.spans
                          if s.path == path and s.start_line <= item.line <= s.end_line]
            if candidates:
                origin, status = candidates[0].origin, "MAPPED"
        normalized = asdict(item)
        normalized["file"] = path if path is not None else item.file
        normalized["origin"] = asdict(origin) if origin else None
        normalized["mapping_status"] = status
        key = digest(normalized)
        unique[key] = MappedCompileDiagnostic(key, item.code, item.severity, item.stage,
                        item.message, normalized["file"], item.line, item.column, origin, status)
    ordered = tuple(sorted(unique.values(), key=lambda d: (
        {"ERROR": 0, "WARNING": 1, "INFO": 2}[d.severity], d.stage, d.file,
        d.line or 0, d.column or 0, d.code, d.diagnostic_id)))
    errors = sum(d.severity == "ERROR" for d in ordered)
    return CompileDiagnosticsReceipt(ordered, errors, sum(d.severity == "WARNING" for d in ordered),
                sum(d.mapping_status != "MAPPED" for d in ordered), source_map.map_sha256,
                errors == 0 and process_exit_code == 0)


def map_build_receipts(*, source_map: GeneratedSourceMap, files: Iterable,
                       typescript=None, lint=None, static_analysis=None, render=None,
                       workspace: str | Path | None = None) -> CompileDiagnosticsReceipt:
    """Adapter for actual pre-existing BUILD-003/004/005/007/008 receipt types."""
    raw: list[RawCompileDiagnostic] = []
    exit_code = 0
    if typescript is not None:
        exit_code = typescript.exit_code
        # Existing BUILD parser drops continuation messages; parse its original logs here.
        parsed = parse_compile_output(typescript.stdout + "\n" + typescript.stderr)
        raw.extend(parsed or (RawCompileDiagnostic(d.code, "ERROR", "typescript", d.message,
                    d.file, d.line, d.column) for d in typescript.diagnostics))
        if not typescript.passed and exit_code == 0:
            raw.append(RawCompileDiagnostic("COMP_TSC_RECEIPT_INCONSISTENT", "ERROR",
                                           "typescript", "TypeScript receipt has conflicting status."))
    if lint is not None:
        raw.extend(RawCompileDiagnostic(i.code, i.severity, "lint", i.message, i.path, i.line)
                   for i in lint.issues)
        if not lint.passed and not any(i.severity == "ERROR" for i in lint.issues):
            raw.append(RawCompileDiagnostic("COMP_LINT_FAILED", "ERROR", "lint", "Lint failed without a mapped error."))
    if static_analysis is not None:
        raw.extend(RawCompileDiagnostic(i.code, "ERROR" if i.severity == "BLOCKER" else "WARNING",
                   "static-analysis", i.message, i.path, i.line) for i in static_analysis.findings)
        if not static_analysis.passed and not any(i.severity == "BLOCKER" for i in static_analysis.findings):
            raw.append(RawCompileDiagnostic("COMP_STATIC_FAILED", "ERROR", "static-analysis", "Static analysis failed."))
    if render is not None and not render.passed:
        raw.append(RawCompileDiagnostic(render.failure_code or "COMP_RENDER_FAILED", "ERROR", "render",
                  "; ".join(render.errors) or "Render failed without diagnostic text."))
    return map_compile_diagnostics(raw, source_map=source_map, files=files,
                                    workspace=workspace, process_exit_code=exit_code)
