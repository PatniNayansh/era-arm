#!/usr/bin/env bash
# Reproducible environment setup for the E.R.A. x VLA project.
# Target OS: Ubuntu 24.04 LTS (WSL2 now; native later). Run from the repo root.
# Grows as we build each layer. Every line here has been run and verified by hand first.
set -euo pipefail

echo "==> System dependencies (build tools + video libraries)"
sudo apt update
sudo apt install -y build-essential cmake pkg-config git curl wget python3-dev
sudo apt install -y ffmpeg libavformat-dev libavcodec-dev libavdevice-dev \
    libavutil-dev libswscale-dev libswresample-dev libavfilter-dev

echo "==> Verifying ffmpeg has the libsvtav1 encoder (needed for dataset recording)"
if ffmpeg -encoders 2>/dev/null | grep -q libsvtav1; then
    echo "    OK: libsvtav1 present"
else
    echo "    WARNING: libsvtav1 missing — add ppa:ubuntuhandbook1/ffmpeg7 (see decisions.md)"
fi

echo "==> Installing uv (pinned Python + dependency manager)"
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
else
    echo "    OK: uv already installed"
fi

echo "==> Installing pinned Python 3.12 and syncing project dependencies"
uv python install 3.12
uv sync

echo "==> Done. Run 'uv run <command>' to use the project's isolated environment."
