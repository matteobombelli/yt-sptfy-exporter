# yt-sptfy-exporter

A simple desktop app that downloads songs from a **Spotify** or **YouTube** playlist — or a single song link — as audio files.

- **YouTube URL** (playlist or video) → downloaded directly.
- **Spotify URL** (playlist or track) → track metadata is fetched from Spotify, then each track is matched against **YouTube** search results (title similarity + duration). The highest-scoring of the YouTube search results is downloaded only if it clears the strictness threshold; otherwise the track is skipped and listed at the end.

Files are tagged with Title, Artist, and Album metadata plus an embedded cover image — from Spotify for Spotify links, and from YouTube (thumbnail center-cropped to a square) for YouTube links.

## Options

- **Spotify version** — *No preference* / *Studio* / *Live*. Biases the YouTube match toward studio or live recordings (applies to Spotify links only).
- **Match strictness** — slider from `0` to `1.00` (default `0.70`). The minimum title-similarity score a YouTube result must reach to count as a confident match for a Spotify track. Higher is pickier; lower accepts looser matches. Tracks whose best match falls below the threshold are skipped entirely. Applies to Spotify links only.
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

## Avoiding YouTube rate-limiting

YouTube throttles anonymous downloads by IP. If you grab a large playlist (or run
several at once), you may start seeing `HTTP Error 429`. The fix is to download as a
**logged-in user** — authenticated requests are throttled far less. The app does this
by reading YouTube cookies straight from your browser, so there's no copying or
exporting of cookie files.

1. Log into YouTube in your browser and stay logged in.
2. Tell the app which browser to read cookies from. Open `app.py` and set
   `COOKIES_FROM_BROWSER` (near the top) to your browser:

   ```python
   COOKIES_FROM_BROWSER = ("firefox",)   # or ("chrome",), ("brave",), ("chromium",), ("edge",)
   ```

That's it — the cookies are picked up automatically on the next run.

### If you still get rate-limited

A 429 is **not** treated as a failed track. When one is hit, the app pauses **all**
downloads, waits a 60-second cooldown (`RATE_LIMIT_COOLDOWN` in `app.py`), then
retries — so nothing is skipped just because YouTube throttled you. You'll see
`Pausing all downloads...` followed by `resuming downloads` in the log. If you're
getting throttled constantly, lowering `MAX_WORKERS` reduces how hard the app hits
YouTube in the first place.

If the cookies can't be read at all (wrong browser, not logged in, locked database),
the run **stops immediately** with a `Stopped: Could not read YouTube cookies...`
message rather than silently failing every track — fix the cause below and re-run.

Notes:
- **Firefox** is the most reliable on Linux. Recent **Chrome / Chromium / Brave**
  encrypt their cookie store, which can block extraction on some systems — if it
  fails, log into YouTube in Firefox and use that instead.
- Keep the browser **closed** while downloading if you hit "could not read cookies"
  errors — an open browser can hold a lock on the cookie database.
- If you log out of YouTube in that browser, the cookies go stale and you're back to
  anonymous throttling.
