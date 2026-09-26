#!/usr/bin/env python3
"""Provision the pinned Remotion browser from the retained R04 dependency lock.

No BIE source is edited. This creates a separate tool workspace, not render proof.
The original failure artifact and its lock must match recorded SHA-256 values.
"""
from pathlib import Path
import argparse
import json
import os
import re
import zipfile
from run_comp_r04_slice import Runner, check_lock, npm_environment, require, sha, write_json

ARTIFACT_SHA = "f7e4fec0645a82b0c17971be58b8322fb9a7c84c1cff5f1545baf75ab6009319"
LOCK_SHA = "e445be44573e1cbac454af2987d84f795c43e8bc826be5e86b754ee42073b1c7"
EXPECTED_BROWSER_VERSION = "149.0.7790.0"  # Remotion 4.0.506's managed Chrome Headless Shell.
PREFIX = "r04-first/evidence/"


def restore_inputs(archive: Path, work: Path, evidence: Path) -> tuple[Path, str]:
    require(sha(archive) == ARTIFACT_SHA, "ORIGIN_ARTIFACT_DIGEST_MISMATCH")
    with zipfile.ZipFile(archive) as z:
        require(len(z.namelist()) == len(set(z.namelist())), "DUPLICATE_ARTIFACT_ENTRY")
        manifest = json.loads(z.read(PREFIX + "EVIDENCE_SHA256.json"))
        import hashlib
        for member, destination in (("generated-project-before-install/package.json", "package.json"),
                                    ("package-lock.json", "package-lock.json")):
            data = z.read(PREFIX + member)
            require(hashlib.sha256(data).hexdigest() == manifest[member], "ORIGIN_MEMBER_DIGEST_MISMATCH")
            (work / destination).write_bytes(data)
            (evidence / destination).write_bytes(data)
    lock = work / "package-lock.json"
    require(sha(lock) == LOCK_SHA, "ORIGIN_LOCK_DIGEST_MISMATCH")
    check_lock(json.loads((work / "package.json").read_text()), json.loads(lock.read_text()))
    return lock, sha(work / "package.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-network", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    work, evidence = output / "work", output / "evidence"
    work.mkdir(); evidence.mkdir()
    env = os.environ.copy()
    for key in ("NODE_OPTIONS", "NODE_PATH", "TS_NODE_PROJECT", "GH_TOKEN", "GITHUB_TOKEN"):
        env.pop(key, None)
    env.update(npm_environment(work))
    runner = Runner(evidence, env)
    result = {"passed": False, "accepted": False, "render_verified": False,
              "scope": "MANAGED_BROWSER_PROVISIONING_ONLY", "origin_run_id": 35495874696,
              "origin_artifact_id": 10599699753, "origin_artifact_sha256": ARTIFACT_SHA,
              "package_lock_sha256": LOCK_SHA}
    try:
        lock, package_sha = restore_inputs(args.artifact, work, evidence)
        require(args.allow_network, "NETWORK_PROVISIONING_NOT_AUTHORIZED")
        runner.run("browser-tools-clean-install", ["npm", "ci", "--ignore-scripts", "--include=dev",
            "--include=optional", "--no-audit", "--no-fund", "--fetch-retries=0", "--fetch-timeout=15000"], work, 600)
        for name in ("@remotion/cli", "@remotion/renderer"):
            require(json.loads((work / "node_modules" / name / "package.json").read_text())["version"] == "4.0.506",
                    "BROWSER_TOOL_PIN_MISMATCH")
        cli = work / "node_modules/@remotion/cli/remotion-cli.js"
        runner.run("managed-browser-ensure", ["node", str(cli), "browser", "ensure",
            "--chrome-mode=headless-shell", "--log=info"], work, 300)
        browser_root = work / "node_modules/.remotion/chrome-headless-shell"
        version = (browser_root / "VERSION").read_text().strip()
        require(version == EXPECTED_BROWSER_VERSION, "MANAGED_BROWSER_VERSION_MISMATCH")
        candidates = [p.resolve() for p in browser_root.rglob("chrome-headless-shell")
                      if p.is_file() and not p.is_symlink() and os.access(p, os.X_OK)]
        require(len(candidates) == 1, "MANAGED_BROWSER_EXECUTABLE_COUNT")
        browser = candidates[0]
        require(browser.is_relative_to(browser_root.resolve()), "BROWSER_OUTSIDE_MANAGED_ROOT")
        observed = runner.run("managed-browser-version", [str(browser), "--version"], work).strip()
        require(EXPECTED_BROWSER_VERSION in observed, "BROWSER_REPORTED_VERSION_MISMATCH")
        require(sha(lock) == LOCK_SHA and sha(work / "package.json") == package_sha, "PROVISIONING_INPUT_MUTATED")
        result.update({"passed": True, "browser_path": str(browser), "browser_sha256": sha(browser),
                       "browser_version": observed, "managed_version_file": version})
        (evidence / "BROWSER_PATH.txt").write_text(str(browser) + "\n")
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        result.update({"failure": str(exc), "failed_stage": runner.stage})
    write_json(evidence / "BROWSER_PROVISION_RESULT.json", result)
    write_json(evidence / "EVIDENCE_SHA256.json", {str(p.relative_to(evidence)): sha(p)
               for p in evidence.rglob("*") if p.is_file()})
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
