#!/usr/bin/env python3
"""Opt-in R04 validation of ONE existing BIE fixture. Never edits canonical source.

Requires the inspected clean checkout and the existing hosted-worker tool profile.
Uses BIE's unchanged checked publisher and actual render validator. No mock renderer.
A captured lock is not a pre-existing approved lock. No result grants acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
from fractions import Fraction
from typing import Any

SOURCE_SHA = "16d4d87824e77db3565a231a332e7977d39d7117"
SOURCE_TREE = "81febee6c9867648b58e0fc16464038b5ac4d12f"
FIXTURE_BLOB = "6aca7cc9876fde0bab55e6bd5d25d087116d2653"
REQUIRED = {"react": "19.0.0", "react-dom": "19.0.0", "remotion": "4.0.506",
            "@remotion/cli": "4.0.506", "@remotion/media": "4.0.506", "typescript": "5.9.3"}
FONT_SUFFIXES = {".ttf", ".otf", ".woff", ".woff2", ".ttc"}


def exclude_font_binaries(_path: str, names: list[str]) -> list[str]:
    """Retain asset hashes, never export font binaries with evidence."""
    return [name for name in names if Path(name).suffix.lower() in FONT_SUFFIXES]


def sha(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def npm_environment(work: Path) -> dict[str, str]:
    """Use distinct empty config files: npm rejects double-loading one path."""
    user_config = work / "npm-user.npmrc"
    global_config = work / "npm-global.npmrc"
    for config in (user_config, global_config):
        with config.open("x", encoding="utf-8"):
            pass
    return {"npm_config_registry": "https://registry.npmjs.org/",
            "npm_config_userconfig": str(user_config),
            "npm_config_globalconfig": str(global_config),
            "npm_config_cache": str(work / "npm-cache")}


def check_lock(package: dict, lock: dict) -> dict:
    """Validate resolution identities, not the security of third-party source code."""
    require(lock.get("lockfileVersion") == 3, "LOCKFILE_V3_REQUIRED")
    packages = lock.get("packages", {})
    root = packages.get("", {})
    for group in ("dependencies", "devDependencies"):
        require(root.get(group, {}) == package.get(group, {}), "LOCK_ROOT_SPEC_MISMATCH:" + group)
    declared = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    for name, version in REQUIRED.items():
        require(declared.get(name) == version, "GOVERNED_PIN_MISMATCH:" + name)
    direct = {}
    for name, spec in declared.items():
        item = packages.get("node_modules/" + name, {})
        version = item.get("version", "")
        require(bool(re.fullmatch(r"\d+\.\d+\.\d+(?:-[\w.-]+)?(?:\+[\w.-]+)?", version)),
                "UNRESOLVED_DIRECT_DEPENDENCY:" + name)
        if re.fullmatch(r"\d+\.\d+\.\d+", str(spec)):
            require(version == spec, "LOCK_PIN_MISMATCH:" + name)
        direct[name] = {"requested": spec, "resolved": version}
    for name in ("@types/react", "@types/react-dom"):
        require(name in direct and direct[name]["resolved"].startswith("19."), "REACT_TYPES_MAJOR_MISMATCH:" + name)
    for key, item in packages.items():
        if not key:
            continue
        require(not item.get("link"), "LINK_DEPENDENCY_FORBIDDEN:" + key)
        require(bool(item.get("version")) and bool(item.get("integrity")), "LOCK_INTEGRITY_MISSING:" + key)
        require(str(item.get("resolved", "")).startswith("https://registry.npmjs.org/"),
                "UNREVIEWED_DEPENDENCY_ORIGIN:" + key)
        name = key.rsplit("node_modules/", 1)[-1]
        if name == "remotion" or name.startswith("@remotion/"):
            require(item["version"] == "4.0.506", "REMOTION_VERSION_MISMATCH:" + key)
    return direct


def check_harness(result: dict) -> None:
    require(result.get("passed") is True, "HARNESS_DID_NOT_PASS:" + str(result.get("failure")))
    require(result.get("accepted") is False, "ACCEPTANCE_BOUNDARY_CHANGED")
    require(result.get("scope") == "CHECKED_SCENE_IR_TECHNICAL_EXECUTION", "HARNESS_SCOPE_CHANGED")
    for name in ("checked-source", "full-pinned-typecheck", "real-cli-composition-discovery", "smoke", "full"):
        matches = [x for x in result.get("stages", []) if x.get("stage") == name]
        require(len(matches) == 1 and matches[0].get("passed") is True, "MISSING_PASS_STAGE:" + name)
    require(result.get("real_book_e2e") == "NOT_RUN", "UNEXPECTED_BOOK_ACCEPTANCE_CLAIM")


def check_media(raw: dict, frames: int) -> None:
    streams = raw.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video"]
    require(len(videos) == 1, "VIDEO_STREAM_COUNT")
    v = videos[0]
    require(v.get("codec_name") == "h264", "VIDEO_CODEC_MISMATCH")
    require((v.get("width"), v.get("height")) == (1280, 720), "VIDEO_SIZE_MISMATCH")
    require(Fraction(v.get("avg_frame_rate", "0")) == 24, "VIDEO_FPS_MISMATCH")
    require(int(v.get("nb_read_frames", -1)) == frames, "DECODED_FRAME_COUNT_MISMATCH")
    duration = float(v.get("duration", "nan"))
    require(math.isfinite(duration) and abs(duration - frames / 24) <= 1 / 24, "VIDEO_DURATION_MISMATCH")
    require(any(s.get("codec_type") == "audio" for s in streams), "EXPECTED_AUDIO_STREAM_MISSING")


class Runner:
    def __init__(self, evidence: Path, env: dict[str, str]):
        self.evidence = evidence
        self.env = env
        self.stage = "preflight"
        self.commands: list[dict] = []

    def run(self, name: str, argv: list[str], cwd: Path, timeout: float = 180) -> str:
        self.stage = name
        out = self.evidence / "logs" / (name + ".stdout.txt")
        err = self.evidence / "logs" / (name + ".stderr.txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        record: dict = {"stage": name, "argv": argv, "cwd": str(cwd), "execution_kind": "REAL_CHILD_PROCESS"}
        start = time.monotonic()
        try:
            with out.open("wb") as stdout, err.open("wb") as stderr:
                p = subprocess.Popen(argv, cwd=cwd, env=self.env, stdout=stdout, stderr=stderr, start_new_session=True)
                reason = None
                while p.poll() is None:
                    if time.monotonic() - start > timeout:
                        reason = "TIMEOUT"
                    elif out.stat().st_size + err.stat().st_size > 32 * 1024 * 1024:
                        reason = "LOG_BUDGET_EXCEEDED"
                    if reason:
                        try:
                            os.killpg(p.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        break
                    time.sleep(0.1)
                record["returncode"] = p.wait()
                record["termination"] = reason
            record["elapsed_seconds"] = round(time.monotonic() - start, 3)
            self.commands.append(record)
            write_json(self.evidence / "COMMANDS.json", self.commands)
            require(out.stat().st_size + err.stat().st_size <= 32 * 1024 * 1024, "LOG_BUDGET_EXCEEDED:" + name)
            require(record["returncode"] == 0 and reason is None, "COMMAND_FAILED:" + name)
            return out.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            record["failure"] = str(e)
            self.commands.append(record)
            write_json(self.evidence / "COMMANDS.json", self.commands)
            raise


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path, help="New directory OUTSIDE the repository")
    p.add_argument("--browser", required=True, type=Path, help="Existing operator-controlled absolute browser binary")
    p.add_argument("--allow-network", action="store_true", help="Explicit permission for npm lock resolution/install")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--bootstrap-lock", action="store_true", help="Explicit first resolution of existing ranges; not prior approval")
    group.add_argument("--lockfile", type=Path, help="Reuse the retained lock from a previous reviewed run")
    p.add_argument("--expected-lock-sha256", help="Required with --lockfile")
    args = p.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    require(not output.is_relative_to(repo), "OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    output.mkdir(parents=True, exist_ok=False)
    evidence, work = output / "evidence", output / "work"
    evidence.mkdir(); work.mkdir()
    project = work / "project"
    env = os.environ.copy()
    for key in ("NODE_OPTIONS", "NODE_PATH", "TS_NODE_PROJECT"):
        env.pop(key, None)
    env.update({"PYTHONPATH": str(repo), "PYTHONDONTWRITEBYTECODE": "1", "CI": "true",
                **npm_environment(work)})
    runner = Runner(evidence, env)
    summary: dict = {"schema_version": "bie.r04.fixture-attempt.v1", "expected_repository_sha": SOURCE_SHA,
                    "expected_repository_tree": SOURCE_TREE, "fixture": "examples/comp_h6/scene.json",
                    "scope": "ONE_SYNTHETIC_CHECKED_FIXTURE", "technical_execution_passed": False,
                    "frame_visual_inspection": "NOT_PERFORMED_BY_THIS_RUNNER", "real_book_e2e": "NOT_RUN",
                    "learning_quality": "NOT_EVALUATED", "game_runtime": "NOT_RUN", "accepted": False,
                    "r04_global_closure": False, "baseline_regression_rerun": "NOT_RUN_BY_THIS_HELPER"}
    source_hashes: dict[str, str] = {}
    try:
        require(repo.is_dir(), "REPOSITORY_MISSING")
        observed_sha = runner.run("source-head", ["git", "rev-parse", "HEAD"], repo).strip()
        summary["observed_repository_sha"] = observed_sha
        require(observed_sha == SOURCE_SHA, "SOURCE_SHA_CHANGED_REINSPECT")
        observed_tree = runner.run("source-tree", ["git", "rev-parse", "HEAD^{tree}"], repo).strip()
        summary["observed_repository_tree"] = observed_tree
        require(observed_tree == SOURCE_TREE, "SOURCE_TREE_CHANGED")
        require(not runner.run("source-clean-before", ["git", "status", "--porcelain", "--untracked-files=all"], repo).strip(), "SOURCE_CHECKOUT_NOT_CLEAN")
        require(sys.version_info[:3] == (3, 13, 5), "PYTHON_PROFILE_MISMATCH")
        require(runner.run("node-version", ["node", "--version"], repo).strip() == "v22.16.0", "NODE_PROFILE_MISMATCH")
        require(runner.run("npm-version", ["npm", "--version"], repo).strip() == "10.9.2", "NPM_PROFILE_MISMATCH")
        require(runner.run("source-parser-version", ["tsc", "--version"], repo).strip() == "Version 5.8.3", "SOURCE_AST_PROFILE_MISMATCH")
        require(args.browser.is_absolute() and args.browser.is_file() and os.access(args.browser, os.X_OK), "BROWSER_REQUIRED")
        browser = args.browser.resolve()
        write_json(evidence / "BROWSER_IDENTITY.json", {"path": str(browser), "sha256": sha(browser),
            "version": runner.run("browser-version", [str(browser), "--version"], repo).strip(),
            "production_isolation_certified": False})
        fixture = repo / "examples/comp_h6/scene.json"
        require(runner.run("fixture-blob", ["git", "hash-object", str(fixture)], repo).strip() == FIXTURE_BLOB, "FIXTURE_BYTES_CHANGED")
        doc = json.loads(fixture.read_text(encoding="utf-8"))
        require(doc["duration_ms"] == 2000 and doc["accepted"] is False, "FIXTURE_SCOPE_CHANGED")
        for asset in doc["metadata"]["compiler_h6"]["audio_assets"]:
            path = repo / "examples/comp_h6/assets" / asset["public_path"]
            require(path.is_file() and not path.is_symlink(), "ORIGINAL_AUDIO_ASSET_MISSING")
            require(sha(path) == asset["sha256"] and path.stat().st_size == asset["byte_length"], "ORIGINAL_AUDIO_ASSET_CHANGED")
        runner.run("checked-source-publication", [sys.executable, "-B", "scripts/compile_scene_checked.py",
            str(fixture), str(project), "--asset-root", str(repo / "examples/comp_h6/assets"),
            "--width", "1280", "--height", "720", "--fps", "24"], repo, 300)
        source_hashes = {str(x.relative_to(project)): sha(x) for x in project.rglob("*") if x.is_file()}
        write_json(evidence / "GENERATED_SOURCE_SHA256.json", source_hashes)
        shutil.copytree(project, evidence / "generated-project-before-install", ignore=exclude_font_binaries)
        package_path = project / "package.json"
        package = json.loads(package_path.read_text())
        lock_path = project / "package-lock.json"
        require(args.allow_network, "NETWORK_INSTALL_NOT_AUTHORIZED")
        flags = ["--ignore-scripts", "--include=dev", "--include=optional", "--no-audit", "--no-fund", "--fetch-retries=0", "--fetch-timeout=15000"]
        if args.lockfile:
            require(bool(args.expected_lock_sha256) and bool(re.fullmatch(r"[0-9a-f]{64}", args.expected_lock_sha256)), "EXPECTED_LOCK_SHA256_REQUIRED")
            require(args.lockfile.is_file() and not args.lockfile.is_symlink(), "LOCKFILE_MISSING")
            require(sha(args.lockfile) == args.expected_lock_sha256, "INPUT_LOCK_HASH_MISMATCH")
            require(not lock_path.exists(), "GENERATED_LOCK_ALREADY_EXISTS_REVIEW_REQUIRED")
            shutil.copyfile(args.lockfile, lock_path)
            summary["lock_origin"] = "EXPLICIT_REPLAY_BY_HASH"
        elif not lock_path.exists():
            require(args.bootstrap_lock, "LOCKFILE_MISSING_BOOTSTRAP_NOT_AUTHORIZED")
            runner.run("lock-bootstrap", ["npm", "install", "--package-lock-only", *flags], project, 300)
            summary["lock_origin"] = "FIRST_RESOLUTION_NOT_PREEXISTING_APPROVAL"
        else:
            summary["lock_origin"] = "GENERATED_EXISTING_LOCK"
        lock = json.loads(lock_path.read_text())
        direct = check_lock(package, lock)
        lock_sha = sha(lock_path)
        summary["package_lock_sha256"] = lock_sha
        shutil.copyfile(lock_path, evidence / "package-lock.json")
        write_json(evidence / "RESOLVED_DIRECT_DEPENDENCIES.json", direct)
        runner.run("clean-pinned-install", ["npm", "ci", *flags], project, 600)
        require(sha(lock_path) == lock_sha, "NPM_CI_MUTATED_LOCK")
        require(json.loads(package_path.read_text()) == package, "PACKAGE_SPEC_MUTATED")
        for name, identity in direct.items():
            installed = json.loads((project / "node_modules" / name / "package.json").read_text())
            require(installed.get("version") == identity["resolved"], "INSTALLED_LOCK_MISMATCH:" + name)
        runner.run("installed-tree", ["npm", "ls", "--all", "--json"], project, 90)
        runner.run("remotion-versions", ["node", str(project / "node_modules/@remotion/cli/remotion-cli.js"), "versions"], project, 90)
        # Do not pass --install: dependencies were installed via the exact retained lock above.
        runner.run("existing-checked-render-harness", [sys.executable, "-B", "scripts/validate_checked_remotion.py",
            str(project), "--browser", str(browser), "--timeout", "300"], repo, 1000)
        reports = list((project / "validation-runs").glob("*/VALIDATION_RESULT.json"))
        require(len(reports) == 1, "VALIDATION_RESULT_COUNT")
        result = json.loads(reports[0].read_text())
        check_harness(result)
        run_id = result["run_id"]
        require(bool(re.fullmatch(r"checked-[0-9a-f]{16}", run_id)), "INVALID_RUN_ID")
        for mode, frames in (("smoke", 12), ("full", 48)):
            media = project / "out" / f"{run_id}-{mode}.mp4"
            require(media.is_file() and media.stat().st_size > 0, "RENDER_FILE_MISSING:" + mode)
            raw = runner.run(mode + "-ffprobe", ["ffprobe", "-v", "error", "-count_frames",
                "-show_streams", "-show_format", "-of", "json", str(media)], repo, 90)
            check_media(json.loads(raw), frames)
            runner.run(mode + "-decode", ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(media), "-f", "null", "-"], repo, 90)
        runner.run("full-framemd5", ["ffmpeg", "-nostdin", "-v", "error", "-i",
            str(project / "out" / f"{run_id}-full.mp4"), "-map", "0:v:0", "-pix_fmt", "rgb24", "-f", "framemd5", "-"], repo, 90)
        frames_dir = evidence / "frames"
        frames_dir.mkdir()
        full = project / "out" / f"{run_id}-full.mp4"
        runner.run("extract-all-48-frames", ["ffmpeg", "-nostdin", "-v", "error", "-i", str(full),
            "-map", "0:v:0", "-vsync", "0", "-start_number", "0", str(frames_dir / "%03d.png")], repo, 90)
        require(len(list(frames_dir.glob("*.png"))) == 48, "FRAME_EXTRACTION_COUNT")
        write_json(evidence / "FRAME_REVIEW_PLAN.json", {
            "review_status": "NOT_PERFORMED", "frames_to_inspect": [0, 5, 6, 11, 12, 23, 24, 29, 30, 47],
            "state_event_frames": [12, 30], "caption_intervals_half_open": [[6, 24], [30, 48]],
            "checks": ["Expected literal text/state transitions", "Hindi/Urdu glyphs and clipping",
                       "Caption appearance and gaps", "MP4 plays and technical tone is audible"],
            "spoken_narration_verified": False, "accepted": False})
        require(all((project / key).is_file() and sha(project / key) == value for key, value in source_hashes.items()), "GENERATED_SOURCE_MUTATED")
        require(sha(lock_path) == lock_sha, "FINAL_LOCK_MUTATED")
        require(not runner.run("source-clean-after", ["git", "status", "--porcelain", "--untracked-files=all"], repo).strip(), "CANONICAL_SOURCE_MUTATED")
        summary.update({"status": "TECHNICAL_EXECUTION_PASSED_REVIEW_AND_REPLAY_PENDING",
                        "technical_execution_passed": True, "pinned_compile_verified": True,
                        "real_composition_discovery_verified": True, "real_smoke_and_full_render_verified": True,
                        "decoded_frame_counts": {"smoke": 12, "full": 48}, "canonical_source_unchanged": True})
    except (OSError, ValueError, TypeError, KeyError, ZeroDivisionError) as e:
        summary.update({"status": "BLOCKED_OR_FAILED", "failed_stage": runner.stage, "failure": str(e)})
    finally:
        # Preserve authentic harness failures too; never package node_modules, caches or font binaries.
        try:
            for name in ("validation-runs", "render-evidence", "out"):
                if (project / name).exists():
                    shutil.copytree(project / name, evidence / name, dirs_exist_ok=True,
                                    ignore=exclude_font_binaries)
            if (project / "package-lock.json").is_file() and not (evidence / "package-lock.json").exists():
                shutil.copyfile(project / "package-lock.json", evidence / "package-lock.json")
        except OSError as e:
            summary.update({"status": "EVIDENCE_EXPORT_FAILED", "technical_execution_passed": False, "export_failure": str(e)})
        write_json(evidence / "R04_SLICE_RESULT.json", summary)
        hashes = {str(x.relative_to(evidence)): sha(x) for x in evidence.rglob("*") if x.is_file()}
        write_json(evidence / "EVIDENCE_SHA256.json", hashes)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["technical_execution_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
