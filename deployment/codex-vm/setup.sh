#!/usr/bin/env bash
# BIE Codex machine setup (Task 044). Run once, as root, on a fresh Ubuntu 24.04 machine that Navin owns:
#
#   curl -fsSL https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/main/deployment/codex-vm/setup.sh | sudo bash
#
# It installs Python, git, Node and OpenAI's Codex CLI, clones the (public) repository, creates the "bie"
# user and the systemd timer that runs tools/codex_vm.py poll. It asks for nothing and stores no secret;
# `sudo bie-setup` afterwards asks for the Gemini key, adds the GitHub deploy key and signs Codex in.
set -euo pipefail

CODEX_VERSION="0.162.1"          # pinned; move only in a reviewed PR
REPO_HTTPS="https://github.com/SEENAV01/Enterprise-bie.git"
BIE_HOME=/var/lib/bie

if [ "$(id -u)" != "0" ]; then echo "Run as root (sudo)."; exit 1; fi
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git curl ca-certificates openssh-client bubblewrap nodejs npm \
  fonts-noto-core >/dev/null
fallocate -l 2G /swapfile 2>/dev/null && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile \
  && echo '/swapfile none swap sw 0 0' >> /etc/fstab || true

id bie >/dev/null 2>&1 || useradd --system --create-home --home-dir "$BIE_HOME" --shell /bin/bash bie
install -d -o bie -g bie -m 700 "$BIE_HOME" "$BIE_HOME/codex" "$BIE_HOME/runs" "$BIE_HOME/done"
install -d -o root -g bie -m 750 /etc/bie
[ -f /etc/bie/bie.env ] || install -o root -g bie -m 640 /dev/null /etc/bie/bie.env

npm install -g --no-audit --no-fund "@openai/codex@${CODEX_VERSION}" >/dev/null
codex --version

if [ -d "$BIE_HOME/repo/.git" ]; then
  sudo -u bie git -C "$BIE_HOME/repo" fetch -q origin main
  sudo -u bie git -C "$BIE_HOME/repo" checkout -q --detach origin/main
else
  sudo -u bie git clone -q "$REPO_HTTPS" "$BIE_HOME/repo"
fi
[ -x "$BIE_HOME/venv/bin/python" ] || sudo -u bie python3 -m venv "$BIE_HOME/venv"
sudo -u bie "$BIE_HOME/venv/bin/pip" install -q --upgrade pip
sudo -u bie "$BIE_HOME/venv/bin/pip" install -q -e "$BIE_HOME/repo[document-intelligence,document-intelligence-layout]"

install -m 755 "$BIE_HOME/repo/deployment/codex-vm/bie-setup" /usr/local/bin/bie-setup
install -m 644 "$BIE_HOME/repo/deployment/codex-vm/bie-codex-poll.service" /etc/systemd/system/
install -m 644 "$BIE_HOME/repo/deployment/codex-vm/bie-codex-poll.timer" /etc/systemd/system/
systemctl daemon-reload

echo
echo "BIE machine ready. Next, once: sudo bie-setup"
