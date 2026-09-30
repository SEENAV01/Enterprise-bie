#!/usr/bin/env python3
"""Actual-browser smoke for Section 18 Batch 001 UI/API control flow."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "productization" / "document_intelligence"
sys.path.insert(0, str(FIXTURES))
from structural_pdf_fixtures import hierarchy_pdf_with_outline


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wait_health(url: str, process: subprocess.Popen, seconds: int = 20) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("server_exited_before_health")
        try:
            with urlopen(url + "/healthz", timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("server_health_timeout")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--browser", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)
    browser_path = Path(args.browser).resolve()
    if not browser_path.is_file() or browser_path.is_symlink():
        raise SystemExit("BROWSER_MUST_BE_RESOLVED_REGULAR_FILE")
    raw = browser_path.read_bytes()
    if raw[:4] != b"\x7fELF":
        raise SystemExit("BROWSER_MUST_BE_NATIVE_ELF")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        pdf = tmp_path / "section18-structural.pdf"
        pdf.write_bytes(hierarchy_pdf_with_outline())
        data_root = tmp_path / "data"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]

        env = {
            **os.environ,
            "BIE_DATA_ROOT": str(data_root),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        server = subprocess.Popen(
            [
                sys.executable, "-B", "-m", "uvicorn", "apps.api.main:app",
                "--host", "127.0.0.1", "--port", str(port),
                "--log-level", "warning",
            ],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        base = f"http://127.0.0.1:{port}"
        observations = []
        try:
            wait_health(base, server)
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    executable_path=str(browser_path),
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                    timeout=120000,
                )
                context = browser.new_context(viewport={"width": 1280, "height": 900})
                page = context.new_page()
                page.goto(base + "/app/", wait_until="networkidle", timeout=30000)
                if page.locator("h1").inner_text() != "Operator Console":
                    raise AssertionError("operator_heading_missing")
                page.locator("#sourceFile").set_input_files(str(pdf))
                page.locator("#validateButton").click()
                page.locator("#sourceMessage").filter(has_text="Source passed").wait_for(timeout=10000)
                if page.locator("#createButton").is_disabled():
                    raise AssertionError("create_not_enabled_after_validation")
                page.locator("#createButton").click()
                page.locator("#runMessage").filter(has_text="State refreshed").wait_for(timeout=15000)
                run_text = page.locator("#runFacts").inner_text()
                if "READY" not in run_text:
                    raise AssertionError("run_not_ready")
                page.get_by_role("button", name="Pause").click()
                page.locator("#runFacts").filter(has_text="PAUSED").wait_for(timeout=10000)
                page.get_by_role("button", name="Resume").click()
                page.locator("#runFacts").filter(has_text="ACTIVE").wait_for(timeout=10000)
                page.get_by_role("button", name="Cancel").click()
                page.locator("#runFacts").filter(has_text="CANCELLED").wait_for(timeout=10000)
                if "cancelled_by_operator" not in page.locator("#failureView").inner_text():
                    raise AssertionError("cancel_evidence_not_visible")
                desktop = out / "operator-desktop.png"
                page.screenshot(path=str(desktop), full_page=True)
                observations.append({
                    "profile": "desktop",
                    "heading": "Operator Console",
                    "run_ready_observed": True,
                    "pause_observed": True,
                    "resume_observed": True,
                    "cancel_observed": True,
                    "safe_failure_evidence_observed": True,
                    "screenshot_sha256": digest(desktop),
                })
                context.close()

                mobile = browser.new_context(viewport={"width": 390, "height": 844})
                page = mobile.new_page()
                page.goto(base + "/app/", wait_until="networkidle", timeout=30000)
                overflow = page.evaluate(
                    "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
                )
                if overflow:
                    raise AssertionError("mobile_horizontal_overflow")
                page.keyboard.press("Tab")
                focused = page.evaluate("() => document.activeElement && document.activeElement.className")
                if "skip-link" not in str(focused):
                    raise AssertionError("skip_link_not_first_keyboard_target")
                shot = out / "operator-mobile.png"
                page.screenshot(path=str(shot), full_page=True)
                observations.append({
                    "profile": "mobile-390x844",
                    "horizontal_overflow": False,
                    "skip_link_keyboard_target": True,
                    "screenshot_sha256": digest(shot),
                })
                mobile.close()
                version = browser.version
                browser.close()
        finally:
            server.terminate()
            try:
                stdout, _ = server.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                stdout, _ = server.communicate(timeout=5)
            (out / "uvicorn.log").write_text(stdout or "", encoding="utf-8")

    result = {
        "schema_version": "bie.section18.batch001.browser-smoke/1",
        "status": "PASS",
        "browser_path": str(browser_path),
        "browser_sha256": hashlib.sha256(raw).hexdigest(),
        "browser_version": version,
        "profiles": observations,
        "actual_http_server": True,
        "actual_browser": True,
        "actual_pdf_upload": True,
        "actual_persisted_run": True,
        "product_accepted": False,
        "section_complete": False,
    }
    (out / "BROWSER_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
