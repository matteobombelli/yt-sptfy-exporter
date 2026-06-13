# yt-sptfy-exporter

A simple desktop app that downloads all songs from a **Spotify** or **YouTube** playlist as MP3 files.

- **YouTube playlist URL** → downloaded directly.
- **Spotify playlist URL** → track metadata is fetched from the Spotify API, each track is matched against YouTube search results (title similarity + duration), and confident matches are downloaded. Tracks without a confident match are skipped and listed at the end.

Songs are saved as `<Title>.mp3`; for Spotify playlists the files are tagged with Title, Artist, and Album metadata.

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
