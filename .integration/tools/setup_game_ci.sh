#!/usr/bin/env bash
# Explicitly approved disposable CI browser setup for Section 15.
set -euo pipefail
python - <<'PY'
from playwright.sync_api import sync_playwright
from pathlib import Path
import importlib.metadata,subprocess
assert importlib.metadata.version('playwright')=='1.57.0'
with sync_playwright() as pw:
    binary=Path(pw.chromium.executable_path)
subprocess.run(['sudo','cp','-a',str(binary.parent),'/opt/bie-game-chromium'],check=True)
subprocess.run(['sudo','ln','-s','/opt/bie-game-chromium/chrome','/usr/local/bin/chromium'],check=True)
PY
sudo tee /etc/apparmor.d/bie-game-validation-chromium >/dev/null <<'PROFILE'
abi <abi/4.0>,
include <tunables/global>
profile bie-game-validation /opt/bie-game-chromium/chrome flags=(unconfined) {
  userns,
}
PROFILE
sudo apparmor_parser -r /etc/apparmor.d/bie-game-validation-chromium
chromium --version
