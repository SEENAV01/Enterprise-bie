"""BUILD-007/008 execution engine with BUILD-009 logs and BUILD-010 integrity.

A successful render is a technical artifact check, never educational acceptance.
Only installed, package-lock-matched local Remotion is executed. Injected runners
are permanently labelled TEST evidence. Source JavaScript must be trusted; use
an external OS/container sandbox for untrusted projects, assets and network I/O.
"""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
from functools import lru_cache
from pathlib import Path
from threading import Event
from typing import Callable, Iterable
import json
import os
import shutil
from .artifact_hashing import canonical_json, confined_path, hash_artifact, hash_artifacts
from .build_common import BuildError
from .dependency_lock import validate_package_lock
from .render_contracts import RenderPlan, RenderReceipt, RenderRequest, make_render_plan, parse_media_probe
from .render_logs import RenderEventLog, redact_text, sanitize
from .render_process import RenderProcessResult, run_bounded_process

ProcessRunner = Callable[..., RenderProcessResult]

class RenderFailure(BuildError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code

def _write_json(path: Path, value: object, secrets: Iterable[str] | None = None) -> None:
    # Do not redact integrity manifests: their canonical hashes bind exact fields.
    payload = sanitize(value, secrets) if secrets is not None else value
    path.write_bytes(canonical_json(payload) + b"\n")

def source_snapshot(root: Path, request: RenderRequest):
    paths = {"package.json", "package-lock.json", "tsconfig.json", request.entrypoint}
    for name in ("remotion.config.ts", "remotion.config.js"):
        if (root / name).exists() or (root / name).is_symlink():
            paths.add(name)
    if request.props_file is not None:
        paths.add(request.props_file)
    for name in ("src", "public"):
        directory = root / name
        if directory.is_symlink():
            raise BuildError("symlink source/asset directory rejected")
        if directory.exists():
            for item in directory.rglob("*"):
                if item.is_symlink():
                    raise BuildError("symlink source/asset rejected")
                if item.is_file():
                    paths.add(item.relative_to(root).as_posix())
    return hash_artifacts(root, paths, binding_sha256=request.scene_fingerprint, allow_empty=True)

def _tool(value: str, name: str) -> str:
    located = shutil.which(value)
    if located is None or not Path(located).is_file():
        raise RenderFailure("TOOL_UNAVAILABLE", f"{name} unavailable")
    return str(Path(located).resolve())

@lru_cache(maxsize=32)
def _binary_sha256(path: str, signature: tuple) -> str:
    hasher = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()

def _binary_identity(path: str) -> str:
    stat = Path(path).stat()
    signature = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    return _binary_sha256(path, signature)

def preflight_toolchain(root: Path, request: RenderRequest) -> dict:
    confined_path(root, request.entrypoint, must_exist=True)
    validate_package_lock(confined_path(root, "package-lock.json", must_exist=True),
                          confined_path(root, "package.json", must_exist=True))
    package = json.loads((root / "package.json").read_text())
    lock = json.loads((root / "package-lock.json").read_text())
    declared = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    versions = {}
    for name in ("remotion", "@remotion/cli", "react", "react-dom"):
        try:
            installed = confined_path(root, f"node_modules/{name}/package.json", must_exist=True)
            metadata = json.loads(installed.read_text())
        except (BuildError, OSError, ValueError) as exc:
            raise RenderFailure("DEPENDENCIES_UNAVAILABLE", f"installed {name} required; no implicit install is permitted") from exc
        version = metadata.get("version")
        locked = lock.get("packages", {}).get(f"node_modules/{name}", {}).get("version")
        if not isinstance(version, str) or version != locked or name not in declared:
            raise RenderFailure("DEPENDENCY_MISMATCH", f"installed/locked {name} mismatch")
        versions[name] = version
    if versions["remotion"] != versions["@remotion/cli"] or versions["react"] != versions["react-dom"]:
        raise RenderFailure("DEPENDENCY_MISMATCH", "Remotion/React package pair versions differ")
    cli_relative = "node_modules/@remotion/cli/remotion-cli.js"
    cli = confined_path(root, cli_relative, must_exist=True)
    node = _tool(request.node_bin, "Node")
    probe = _tool(request.ffprobe_bin, "ffprobe")
    browser = None
    if request.browser_executable is not None:
        browser = _tool(request.browser_executable, "browser")
    if request.props_file:
        props = confined_path(root, request.props_file, must_exist=True)
        if props.stat().st_size > 2 * 1024 * 1024:
            raise BuildError("props file exceeds 2 MiB contract")
        # Validate finite JSON without changing the actual input bytes.
        canonical_json(json.loads(props.read_text()))
    return {"versions": versions, "node": node, "ffprobe": probe, "browser": browser,
            "cli": str(cli), "cli_sha256": hash_artifact(root, cli_relative).sha256,
            "node_sha256": _binary_identity(node), "ffprobe_sha256": _binary_identity(probe),
            "browser_launcher_sha256": _binary_identity(browser) if browser else None}

def build_render_command(request: RenderRequest, plan: RenderPlan, *, cli: str,
                         node: str, staged_output: str, empty_env: str) -> tuple[str, ...]:
    command = [node, cli, "render", str(Path(request.workspace).resolve() / request.entrypoint),
               request.composition.composition_id, staged_output,
               "--codec=h264", "--pixel-format=yuv420p", f"--crf={request.crf}",
               f"--concurrency={request.concurrency}", "--overwrite=false", "--log=info",
               f"--timeout={request.frame_timeout_ms}", "--bundle-cache=false", f"--env-file={empty_env}"]
    if plan.mode == "smoke":
        command.append(f"--frames={plan.first_frame}-{plan.last_frame}")
    if request.browser_executable is not None:
        command.append(f"--browser-executable={request.browser_executable}")
    if request.props_file is not None:
        command.append(f"--props={Path(request.workspace).resolve() / request.props_file}")
    return tuple(command)

def _persist_process(attempt: Path, stage: str, result: RenderProcessResult,
                     secrets: Iterable[str]) -> None:
    _write_json(attempt / f"{stage}-process.json", asdict(result), secrets)
    (attempt / f"{stage}.stdout.log").write_text(redact_text(result.process.stdout, secrets), encoding="utf-8")
    (attempt / f"{stage}.stderr.log").write_text(redact_text(result.process.stderr, secrets), encoding="utf-8")

def execute_render(request: RenderRequest, plan: RenderPlan, *,
                   cancel_event: Event | None = None, secrets: Iterable[str] = (),
                   runner: ProcessRunner | None = None) -> RenderReceipt:
    expected_plan = make_render_plan(request, plan.mode, first_frame=plan.first_frame,
                                     frame_count=plan.expected_frames if plan.mode == "smoke" else None)
    if plan != expected_plan:
        raise BuildError("inconsistent or forged render plan")
    root = Path(request.workspace).absolute()
    if root.is_symlink() or not root.is_dir():
        raise BuildError("workspace missing or symlink")
    root = root.resolve()
    # Validate paths before any attempt writes. Never overwrite a previous run.
    output = confined_path(root, request.output_path)
    evidence_root = confined_path(root, "render-evidence")
    evidence_root.mkdir(exist_ok=True)
    attempt = confined_path(root, f"render-evidence/{request.run_id}")
    attempt.mkdir(mode=0o700, exist_ok=False)
    evidence_relative = attempt.relative_to(root).as_posix()
    secrets = tuple(secrets)
    execute = runner or run_bounded_process
    execution_kind = "LOCAL_REMOTION_CLI" if runner is None else "INJECTED_TEST_RUNNER"
    passed = False
    failure_code = None
    errors: tuple[str, ...] = ()
    media = None
    input_sha = recipe_sha = None
    started = False
    verified_output = None
    published = False
    staged = attempt / "staged.mp4"
    with RenderEventLog(attempt / "events.jsonl", request.run_id, secrets=secrets) as log:
        log.append("created", "STARTED", {"mode": plan.mode, "execution_kind": execution_kind})
        try:
            if cancel_event is not None and cancel_event.is_set():
                raise RenderFailure("CANCELLED", "cancelled before preflight")
            if output.exists():
                raise RenderFailure("OUTPUT_EXISTS", "refusing to overwrite existing output")
            if runner is None:
                package_path = confined_path(root, "package.json", must_exist=True)
                if json.loads(package_path.read_text()).get("bie_test_fixture") is True:
                    raise RenderFailure("TEST_FIXTURE_REJECTED", "test fixture cannot use the production execution path")
            if runner is None:
                from .checked_scene_compile import verify_checked_workspace
                from .generated_code_regression import typecheck_generated_workspace
                try:
                    checked = verify_checked_workspace(root, expected_scene_fingerprint=request.scene_fingerprint, render_request=request)
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    raise RenderFailure("SOURCE_QA_BLOCKED", str(exc)) from exc
                _write_json(attempt / "source-qa.json", asdict(checked))
                typecheck = typecheck_generated_workspace(root)
                _write_json(attempt / "full-typecheck.json", asdict(typecheck))
                if typecheck.status != "PASS":
                    raise RenderFailure("FULL_TYPECHECK_BLOCKED", "Pinned generated project typecheck did not pass: " + typecheck.status)
                # H3 is mandatory before any real Remotion CLI source execution.
                from .hardened_scene_compile import require_h3_workspace
                try:
                    require_h3_workspace(root, expected_scene_fingerprint=request.scene_fingerprint, render_request=request)
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    raise RenderFailure("H3_SOURCE_QA_BLOCKED", str(exc)) from exc
            initial = source_snapshot(root, request)
            input_sha = initial.manifest_sha256
            _write_json(attempt / "input-manifest.json", asdict(initial))
            tools = preflight_toolchain(root, request)
            _write_json(attempt / "toolchain.json", tools)
            recipe = {"schema_version": "bie.render-recipe.v1", "scene_fingerprint": request.scene_fingerprint,
                      "input_sha256": input_sha, "composition": asdict(request.composition),
                      "plan": asdict(plan), "codec": "h264", "pixel_format": "yuv420p", "crf": request.crf,
                      "concurrency": request.concurrency, "frame_timeout_ms": request.frame_timeout_ms,
                      "require_audio": request.require_audio, "props_file": request.props_file,
                      "tool_versions": tools["versions"], "cli_sha256": tools["cli_sha256"],
                      "node_sha256": tools["node_sha256"], "ffprobe_sha256": tools["ffprobe_sha256"],
                      "browser_launcher_sha256": tools["browser_launcher_sha256"]}
            recipe_sha = sha256(canonical_json(recipe)).hexdigest()
            _write_json(attempt / "recipe.json", {**recipe, "recipe_sha256": recipe_sha})
            empty_env = attempt / "empty.env"
            empty_env.write_text("", encoding="utf-8")
            command = build_render_command(request, plan, cli=tools["cli"], node=tools["node"],
                                           staged_output=str(staged), empty_env=str(empty_env))
            log.append("preflight", "PASS", {"input_sha256": input_sha, "recipe_sha256": recipe_sha})
            log.append("render", "STARTED", {"expected_frames": plan.expected_frames})
            result = execute(command, cwd=root, timeout_s=request.timeout_s, cancel_event=cancel_event,
                             max_output_bytes=request.max_output_bytes, secrets=secrets)
            started = result.started
            _persist_process(attempt, "render", result, secrets)
            log.append("render", "PASS" if result.process.passed else "FAIL",
                       {"outcome": result.outcome, "exit_code": result.process.exit_code})
            if result.outcome != "SUCCEEDED" or not result.process.passed or result.process.exit_code != 0:
                raise RenderFailure(result.outcome, "renderer process did not succeed")
            confined_path(root, f"{evidence_relative}/staged.mp4", must_exist=True)
            if staged.stat().st_size == 0:
                raise RenderFailure("EMPTY_ARTIFACT", "renderer produced an empty file")
            # Bind probe to the exact bytes eventually published, not a mutable filename.
            media_before = hash_artifact(root, f"{evidence_relative}/staged.mp4")
            probe_command = (tools["ffprobe"], "-v", "error", "-err_detect", "explode", "-count_frames",
                             "-show_streams", "-show_format", "-of", "json", str(staged))
            log.append("probe", "STARTED")
            # Always the same bounded runner, and same evidence-kind for injected tests.
            probe = execute(probe_command, cwd=root, timeout_s=request.timeout_s, cancel_event=cancel_event,
                            max_output_bytes=request.max_output_bytes, secrets=secrets)
            _persist_process(attempt, "probe", probe, secrets)
            if probe.outcome in {"CANCELLED", "TIMED_OUT", "OUTPUT_LIMIT"}:
                raise RenderFailure(probe.outcome, "media probe did not complete")
            if probe.outcome != "SUCCEEDED" or not probe.process.passed or probe.process.stderr.strip():
                raise RenderFailure("MEDIA_PROBE_FAILED", "ffprobe failed or reported decode errors")
            media = parse_media_probe(probe.process.stdout, request, plan)
            media_after = hash_artifact(root, f"{evidence_relative}/staged.mp4")
            if media_before != media_after:
                raise RenderFailure("ARTIFACT_CHANGED", "media changed during probe")
            log.append("probe", "PASS", asdict(media))
            final_inputs = source_snapshot(root, request)
            if final_inputs != initial:
                raise RenderFailure("INPUT_CHANGED", "source/asset/props bytes changed during render")
            if preflight_toolchain(root, request) != tools:
                raise RenderFailure("TOOLCHAIN_CHANGED", "toolchain metadata changed during render")
            if cancel_event is not None and cancel_event.is_set():
                raise RenderFailure("CANCELLED", "cancelled before publication")
            output = confined_path(root, request.output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            # A same-filesystem hard link is exclusive: never replace a pre-existing file.
            os.link(staged, output, follow_symlinks=False)
            published = True
            verified_output = hash_artifact(root, request.output_path)
            if (verified_output.sha256, verified_output.size_bytes) != (media_after.sha256, media_after.size_bytes):
                raise RenderFailure("PUBLISH_MISMATCH", "published bytes differ from probed bytes")
            # Keep the staged hard-link in evidence, so failed sealing can roll back publication.
            log.append("publish", "PASS", {"output": request.output_path, "sha256": verified_output.sha256})
            passed = True
        except (BuildError, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            failure_code = exc.code if isinstance(exc, RenderFailure) else "VALIDATION_OR_IO_FAILED"
            errors = (redact_text(str(exc), secrets),)
            if published:
                # Only remove the new link created by this attempt, never an old artifact.
                try:
                    if staged.exists() and os.path.samefile(staged, output):
                        output.unlink()
                except OSError:
                    pass
            log.append("failure", "FAIL", {"code": failure_code, "message": errors[0]})
        terminal_status = "PASS" if passed else ("CANCELLED" if failure_code == "CANCELLED" else
                         "BLOCKED" if failure_code in {"DEPENDENCIES_UNAVAILABLE", "TOOL_UNAVAILABLE", "SOURCE_QA_BLOCKED", "FULL_TYPECHECK_BLOCKED"} else "FAIL")
        log.append("terminal", terminal_status, {"accepted": False, "failure_code": failure_code})
    receipt = RenderReceipt("bie.render-receipt.v1", request.run_id, plan.mode,
                            request.composition.composition_id, passed, failure_code, errors,
                            request.output_path if passed else None, plan.expected_frames, media,
                            input_sha, recipe_sha, evidence_relative, execution_kind, started,
                            verified_output.sha256 if passed else None,
                            verified_output.size_bytes if passed else None, False)
    try:
        _write_json(attempt / "RENDER_RECEIPT.json", asdict(receipt))
        paths = [p.relative_to(root).as_posix() for p in attempt.rglob("*") if p.is_file()]
        if passed:
            paths.append(request.output_path)
        binding = recipe_sha or input_sha or request.scene_fingerprint
        artifacts = hash_artifacts(root, paths, binding_sha256=binding, allow_empty=True)
        if passed:
            sealed_output = next(a for a in artifacts.artifacts if a.path == request.output_path)
            if sealed_output != verified_output:
                raise BuildError("published media changed during evidence sealing")
            if source_snapshot(root, request) != initial:
                raise BuildError("source changed during evidence sealing")
        _write_json(attempt / "ARTIFACT_MANIFEST.json", asdict(artifacts))
    except (BuildError, OSError, ValueError, TypeError) as exc:
        # An unsealed terminal PASS is NOT a completed receipt. Roll back our link,
        # retain diagnostics, and raise; downstream must require the artifact seal.
        try:
            if published and staged.exists() and output.exists() and os.path.samefile(staged, output):
                output.unlink()
            _write_json(attempt / "EVIDENCE_SEAL_FAILURE.json",
                        {"passed": False, "accepted": False, "error": redact_text(str(exc), secrets)})
        except OSError:
            pass
        raise BuildError("evidence sealing failed; no successful render receipt issued") from exc
    return receipt
