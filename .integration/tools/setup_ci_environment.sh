#!/usr/bin/env bash
# Hosted Ubuntu adapter for the EXISTING BIE namespace worker contract.
# This changes only the disposable verification runner, not product source.
# Do not disable AppArmor globally, use sudo for workloads, or bypass isolation.
set -euo pipefail

test "$(id -u)" -ne 0
: "${pythonLocation:?setup-python must run first}"
: "${GITHUB_WORKSPACE:?}"
: "${RUNNER_TEMP:?}"
: "${GITHUB_PATH:?}"
: "${GITHUB_ENV:?}"
EVIDENCE="$RUNNER_TEMP/bie-ci-setup"
mkdir -p "$EVIDENCE"

# The shipped worker intentionally does not expose arbitrary /opt paths.
# Copy the exact setup-action distributions into its already declared roots.
PY_SOURCE="$(realpath "$pythonLocation")"
NODE_SOURCE="$(dirname "$(dirname "$(realpath "$(command -v node)")")")"
PY_DEST=/opt/pyvenv
NODE_DEST=/opt/nvm/versions/node/v22.16.0
python -c 'import sys; assert sys.version_info[:3] == (3, 13, 5)'
test "$(node --version)" = v22.16.0
test ! -e "$PY_DEST"
test ! -e "$NODE_DEST"
sudo install -d -m 0755 "$PY_DEST" "$NODE_DEST"
sudo cp -a "$PY_SOURCE/." "$PY_DEST/"
sudo cp -a "$NODE_SOURCE/." "$NODE_DEST/"
cmp "$PY_SOURCE/bin/python3.13" "$PY_DEST/bin/python3.13"
cmp "$NODE_SOURCE/bin/node" "$NODE_DEST/bin/node"
sudo chown -R "$(id -u):$(id -g)" "$PY_DEST" "$NODE_DEST"
printf '/opt/pyvenv/lib\n' | sudo tee /etc/ld.so.conf.d/bie-validation-python.conf >/dev/null
sudo ldconfig
export PATH="$PY_DEST/bin:$NODE_DEST/bin:$PATH"
export LD_LIBRARY_PATH="$PY_DEST/lib"
export PYTHONPATH="$GITHUB_WORKSPACE"
python -c 'import sys; assert sys.version_info[:3] == (3, 13, 5); assert sys.prefix == "/opt/pyvenv"; print(sys.executable)'
# A sanitized worker does not inherit LD_LIBRARY_PATH. Test that exact condition.
env -u LD_LIBRARY_PATH /opt/pyvenv/bin/python3.13 -I -c 'import ssl, ctypes, sys; assert sys.version_info[:3] == (3,13,5)'
test "$(node --version)" = v22.16.0
printf '%s\n' "$PY_DEST/bin" "$NODE_DEST/bin" >> "$GITHUB_PATH"
printf 'LD_LIBRARY_PATH=%s\nPYTHONPATH=%s\n' "$PY_DEST/lib" "$GITHUB_WORKSPACE" >> "$GITHUB_ENV"
printf 'python_source=%s\nnode_source=%s\n' "$PY_SOURCE" "$NODE_SOURCE" > "$EVIDENCE/runtime-layout.txt"
sha256sum "$PY_SOURCE/bin/python3.13" "$PY_DEST/bin/python3.13" "$NODE_SOURCE/bin/node" "$NODE_DEST/bin/node" >> "$EVIDENCE/runtime-layout.txt"

python -m pip install -r .integration/tools/requirements-validation.txt 2>&1 | tee "$EVIDENCE/python-install.log"
# Independent projection-reference tests require this declared test-only extra.
# Preserve the sealed compile-worker requirements file without modification.
python -m pip install 'pyproj==3.7.2' 'certifi==2026.5.20' 2>&1 | tee "$EVIDENCE/regression-extras-install.log"
python -m pip check
npm install --global typescript@5.8.3 2>&1 | tee "$EVIDENCE/typescript-install.log"
python -m playwright install --with-deps chromium
sudo apt-get update
sudo apt-get install -y ffmpeg bubblewrap libseccomp2 apparmor apparmor-utils

# Ubuntu's documented per-application permission, not a system-wide disable:
# https://documentation.ubuntu.com/release-notes/24.04/#unprivileged-user-namespace-restrictions
# Only this root-owned executable can attach to the new profile. It has no
# setuid bit or host capabilities. BIE still creates private mount/user/PID/net
# namespaces, drops capabilities and installs its seccomp filter before exec.
UNSHARE_SOURCE="$(realpath "$(command -v unshare)")"
UNSHARE_DIR=/usr/local/libexec/bie-integration
sudo install -d -m 0755 -o root -g root "$UNSHARE_DIR"
sudo install -m 0755 -o root -g root "$UNSHARE_SOURCE" "$UNSHARE_DIR/unshare"
cmp "$UNSHARE_SOURCE" "$UNSHARE_DIR/unshare"
cat > "$EVIDENCE/bie-integration-unshare.apparmor" <<'PROFILE'
abi <abi/4.0>,
include <tunables/global>
profile bie-integration-unshare /usr/local/libexec/bie-integration/unshare flags=(unconfined) {
  userns,
}
PROFILE
sudo install -m 0644 -o root -g root "$EVIDENCE/bie-integration-unshare.apparmor" /etc/apparmor.d/bie-integration-unshare
sudo apparmor_parser -r /etc/apparmor.d/bie-integration-unshare
export PATH="$UNSHARE_DIR:$PATH"
printf '%s\n' "$UNSHARE_DIR" >> "$GITHUB_PATH"
{
  echo 'Application-specific namespace profile installed; no global restriction disabled.'
  sysctl kernel.apparmor_restrict_unprivileged_userns
  sysctl user.max_user_namespaces
  sha256sum "$UNSHARE_SOURCE" "$UNSHARE_DIR/unshare"
  stat -c '%U:%G %a %n' "$UNSHARE_DIR/unshare"
  command -v unshare
  unshare --user --map-root-user --mount --net --pid --fork /bin/sh -c 'test "$(id -u)" = 0; test "$$" = 1; echo USER_MOUNT_NETWORK_PID_NAMESPACES_AVAILABLE'
} 2>&1 | tee "$EVIDENCE/namespace-preflight.log"
python -m pip freeze > "$EVIDENCE/python-freeze.txt"
{ python --version; node --version; tsc --version; ffmpeg -version | head -n 1; } > "$EVIDENCE/tool-versions.txt"
echo 'Hosted runner ready for unchanged source regression and kernel-enforcement tests.'
