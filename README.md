# yt-sptfy-exporter

A simple desktop app that downloads songs from a **Spotify** or **YouTube** playlist — or a single song link — as audio files.

- **YouTube URL** (playlist or video) → downloaded directly.
- **Spotify URL** (playlist or track) → track metadata is fetched from Spotify, each track is matched against YouTube search results (title similarity + duration), and confident matches are downloaded. Tracks without a confident match are skipped and listed at the end.

Files are tagged with Title, Artist, and Album metadata plus an embedded cover image — from Spotify for Spotify links, and from YouTube (thumbnail center-cropped to a square) for YouTube links.

## Options

- **Spotify version** — *No preference* / *Studio* / *Live*. Biases the YouTube match toward studio or live recordings (applies to Spotify links only).
- **Quality** — *128 kbps* / *192 kbps* MP3, or *Best quality (no re-encode)* which keeps YouTube's native audio stream (`.opus`/`.m4a`) untouched.

> On audio quality: YouTube's source audio tops out around 128–160 kbps Opus, so 192 kbps MP3 is already at the source ceiling — higher MP3 bitrates would only add file size, not fidelity. Choose **Best quality** to preserve the source exactly.

## Installation

An install script sets up everything the app needs: [uv](https://docs.astral.sh/uv/) (Python environment management), **ffmpeg** (MP3 conversion and tagging), and **deno** (JS runtime used by yt-dlp for YouTube extraction).

### macOS / Linux

```sh
./install.sh
```

(macOS uses Homebrew for ffmpeg; Linux uses dnf/apt/pacman.)

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

(Uses winget for everything.)

Restart your terminal after installing so the new tools are on your PATH.

## Running

From the project folder:

```sh
uv run app.py
```

On first run, uv automatically creates a virtual environment (`.venv/`) and installs the dependencies.

Paste a playlist or song URL, choose an output folder, and click **Download**.

No Spotify account or API credentials are needed — track metadata is read from the
same public web-player API the Spotify embed widget uses, so only **public**
playlists and tracks work.
