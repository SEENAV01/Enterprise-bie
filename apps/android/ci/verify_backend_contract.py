"""Verify the live loopback API against Android's governed contract fixture."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "apps/android/app/src/test/resources/canonical_api_contract.json"


def main() -> int:
    evidence = Path(sys.argv[1])
    evidence.mkdir(parents=True, exist_ok=True)
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="bie-android-api-smoke-") as data_root:
        env = {**os.environ, "BIE_DATA_ROOT": data_root}
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "scripts/run_bie_api.py"),
             "--host", "127.0.0.1", "--port", "8765"],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 20
            while True:
                if process.poll() is not None:
                    raise RuntimeError("loopback API exited before becoming ready")
                try:
                    health = fetch("http://127.0.0.1:8765/healthz")
                    break
                except (URLError, TimeoutError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError("loopback API readiness timed out") from None
                    time.sleep(0.2)
            capabilities = fetch("http://127.0.0.1:8765/v1/capabilities")
            for name, actual in (("health", health), ("capabilities", capabilities)):
                for key, value in expected[name].items():
                    if actual.get(key) != value:
                        raise RuntimeError(f"governed {name} field mismatch: {key}")
                (evidence / f"safe-{name}.json").write_text(
                    json.dumps(actual, sort_keys=True, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )
            print("Canonical loopback API contract: PASS")
            return 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def fetch(url: str) -> dict[str, object]:
    with urlopen(url, timeout=2) as response:
        if response.status != 200:
            raise RuntimeError("loopback API returned non-200")
        return json.loads(response.read(256 * 1024 + 1))


if __name__ == "__main__":
    raise SystemExit(main())
