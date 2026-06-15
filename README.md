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

Paste a playlist URL, choose an output folder, and click **Download**.

## Spotify API setup

Downloading from Spotify playlists requires free Spotify API credentials:

1. Go to <https://developer.spotify.com/dashboard> and log in with any Spotify account.
2. Click **Create app**. Name it anything, set the Redirect URI to `http://localhost` (required field, not used by this app), and check the **Web API** box.
3. Open the app's **Settings** and copy the **Client ID** and **Client Secret**.
4. Provide them to the app either way:
   - The app prompts for them the first time you submit a Spotify URL, or
   - Edit `config.json` (auto-created next to `app.py` on first run):

   ```json
   {
     "spotify_client_id": "your-client-id",
     "spotify_client_secret": "your-client-secret"
   }
   ```

`config.json` is gitignored, so your credentials stay out of version control.

> Note: the app uses the Client Credentials flow, so only **public** playlists work.

> **Heads-up:** Spotify currently blocks the playlist-tracks endpoint for newly created API apps (HTTP 403). When that happens, the app automatically falls back to the public web-player API (no credentials needed, playlists of any length). The official API path is kept for apps with grandfathered or extended-quota access.
