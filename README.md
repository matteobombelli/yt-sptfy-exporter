# yt-sptfy-exporter

A simple desktop app that downloads songs from a **Spotify** or **YouTube** playlist — or a single song link — as audio files.

- **YouTube URL** (playlist or video) → downloaded directly.
- **Spotify URL** (playlist or track) → track metadata is fetched from Spotify, then each track is matched against search results (title similarity + duration) — **SoundCloud first, then YouTube** as a fallback — and confident matches are downloaded. Tracks without a confident match on either source are skipped and listed at the end.

Files are tagged with Title, Artist, and Album metadata plus an embedded cover image — from Spotify for Spotify links, and from YouTube (thumbnail center-cropped to a square) for YouTube links.

## Options

- **Spotify version** — *No preference* / *Studio* / *Live*. Biases the YouTube match toward studio or live recordings (applies to Spotify links only).
- **Quality**:
  - *128 / 192 kbps MP3* — transcoded to MP3. Universal, but a lossy re-encode of an already-lossy source (some quality is lost).
  - *Best (Opus, lossless)* — keeps YouTube's native Opus stream, repackaged to `.opus`. **No quality loss** and the best fidelity (Opus beats AAC at the same bitrate). Tags and cover art are embedded.
  - *Best (.m4a, lossless)* — copies YouTube's native AAC stream to `.m4a`. No re-encode, plays everywhere, embeds cover art. Slightly lower bitrate source than Opus, and not every video offers it — if it's missing, the log will tell you to use *Best (Opus)* instead.

> Why the MP3 options lose quality: YouTube audio is already compressed (~128–160 kbps Opus), so re-encoding it to MP3 compresses it a second time. The **Best** options avoid this entirely by keeping the original stream. Don't bother going above 192 kbps MP3 — it only adds file size, not fidelity.

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
