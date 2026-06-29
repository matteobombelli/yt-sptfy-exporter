#!/usr/bin/env bash
# Double-click launcher for non-coders (macOS).
# First run installs uv/ffmpeg/deno if missing; every run starts the app.
cd "$(dirname "$0")" || exit 1

# Use freshly-installed tools without needing to restart the terminal.
export PATH="$HOME/.local/bin:$HOME/.deno/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

./install.sh

if ! command -v uv >/dev/null 2>&1; then
    echo
    echo "Setup didn't finish. Read the messages above, then double-click Start again."
    read -n 1 -s -r -p "Press any key to close."
    exit 1
fi

echo
echo "Starting the app..."
uv run app.py
