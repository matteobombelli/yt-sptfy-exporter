#!/usr/bin/env bash
# Installs dependencies for yt-sptfy-exporter: uv, ffmpeg, deno (macOS/Linux)
set -e

if command -v uv >/dev/null 2>&1; then
    echo "uv already installed"
else
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

if command -v ffmpeg >/dev/null 2>&1; then
    echo "ffmpeg already installed"
else
    echo "Installing ffmpeg..."
    if [ "$(uname)" = "Darwin" ]; then
        brew install ffmpeg
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y ffmpeg
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm ffmpeg
    else
        echo "No supported package manager found - install ffmpeg manually." >&2
        exit 1
    fi
fi

if command -v deno >/dev/null 2>&1; then
    echo "deno already installed"
else
    echo "Installing deno (JS runtime used by yt-dlp for YouTube)..."
    curl -fsSL https://deno.land/install.sh | sh -s -- -y
fi

echo
echo "All dependencies installed. Restart your terminal, then run: uv run app.py"
