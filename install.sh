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
        if command -v brew >/dev/null 2>&1; then
            brew install ffmpeg
        else
            # Fresh Mac with no Homebrew: download a static ffmpeg build (no admin needed).
            echo "Homebrew not found; downloading a static ffmpeg build instead..."
            case "$(uname -m)" in
                arm64) ff_url="https://ffmpeg.martin-riedl.de/redirect/latest/macos/arm64/release/ffmpeg.zip" ;;
                *)     ff_url="https://ffmpeg.martin-riedl.de/redirect/latest/macos/amd64/release/ffmpeg.zip" ;;
            esac
            ff_tmp="$(mktemp -d)"
            curl -fsSL "$ff_url" -o "$ff_tmp/ffmpeg.zip"
            unzip -o -q "$ff_tmp/ffmpeg.zip" -d "$ff_tmp"
            mkdir -p "$HOME/.local/bin"
            mv "$(find "$ff_tmp" -name ffmpeg -type f | head -n1)" "$HOME/.local/bin/ffmpeg"
            chmod +x "$HOME/.local/bin/ffmpeg"
            xattr -d com.apple.quarantine "$HOME/.local/bin/ffmpeg" 2>/dev/null || true
            rm -rf "$ff_tmp"
            echo "Installed static ffmpeg to ~/.local/bin"
        fi
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
