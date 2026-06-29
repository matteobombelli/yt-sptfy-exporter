# yt-sptfy-exporter

A simple desktop app that downloads songs from a Spotify or YouTube playlist, or a single song link, as audio files.

- YouTube links (a playlist or a single video) are downloaded directly.
- Spotify links (a playlist or a track) are handled by reading the track metadata from Spotify, then matching each track against YouTube search results by title similarity and duration. The highest scoring result is downloaded only if it clears the strictness threshold; any track that falls short is skipped and listed at the end.

Every file is tagged with its title, artist, and album, and has a cover image embedded. Spotify links use Spotify's artwork, while YouTube links use the video thumbnail cropped to a square from the center.

## Options

- Version (No preference, Studio, or Live): biases the YouTube match toward studio or live recordings. It changes how tracks are matched, so it has no effect on direct YouTube links.
- Match strictness: a slider from 0 to 1.00, with a default of 0.70. This is the lowest title-similarity score a YouTube result may have and still count as a confident match. Higher values are pickier; lower values accept looser matches. Any track whose best match scores below the threshold is skipped. Like the version setting, it applies only to matched tracks, not to direct YouTube links.
- Quality:
  - 128 or 192 kbps MP3: transcoded to MP3. It plays everywhere, but it is a lossy re-encode of an already lossy source, so some quality is lost.
  - Best (Opus, lossless): keeps YouTube's native Opus stream and repackages it as .opus. Nothing is re-encoded, so no quality is lost, and Opus gives the best fidelity (it beats AAC at the same bitrate). Tags and cover art are embedded.
  - Best (.m4a, lossless): copies YouTube's native AAC stream to .m4a with no re-encode. It plays everywhere and embeds cover art. Its source bitrate is slightly lower than Opus, and not every video provides it; when it is missing, the log tells you to use Best (Opus) instead.

A note on the MP3 options: YouTube audio is already compressed (roughly 128 to 160 kbps Opus), so re-encoding it to MP3 compresses it a second time. The Best options avoid this by keeping the original stream untouched. There is no benefit to going above 192 kbps MP3, since it only adds file size, not fidelity.

## Installation

### Easiest: download and double-click (no terminal)

If you don't use GitHub or a terminal, this is the way:

1. Go to the [**Releases**](https://github.com/matteobombelli/yt-sptfy-exporter/releases/latest) page and download **yt-sptfy-exporter.zip** (under *Assets*). No GitHub account needed. Unzip it.
2. Open the unzipped folder and start the app:
   - **macOS:** right-click **Start.command** and choose **Open**, then **Open** again. Right-click only the first time — macOS blocks downloaded scripts until you approve one once; after that a plain double-click works.
   - **Windows:** double-click **Start.bat**. If a blue "Windows protected your PC" box appears, click **More info**, then **Run anyway**.
3. The first run installs everything the app needs (uv, ffmpeg, deno) — on a fresh Mac this needs no Homebrew and no admin password. On Windows it may ask for permission; after setup finishes, double-click **Start.bat** once more to open the app.

Paste a playlist or song link, pick a folder, and click Download. Every later launch is a single double-click. (Linux: use the terminal steps below.)

### Set up from a terminal

The install script sets up everything the app needs: uv for Python environment management, ffmpeg for MP3 conversion and tagging, and deno, the JavaScript runtime that yt-dlp uses for YouTube extraction.

#### macOS / Linux

```sh
./install.sh
```

macOS uses Homebrew for ffmpeg; Linux uses dnf, apt, or pacman.

#### Windows

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

This uses winget for everything.

After installing, restart your terminal so the new tools are on your PATH.

##### Desktop shortcut (optional)

You can launch the app from a desktop icon instead of a terminal:

1. Run `uv run app.py` once (see Running below) so the virtual environment, the `.venv` folder, is created.
2. Right-click the desktop and choose New, then Shortcut.
3. For the location, give the full path to the project's windowed Python followed by the full path to `app.py`. Quote both, for example:

   ```
   "C:\path\to\yt-sptfy-exporter\.venv\Scripts\pythonw.exe" "C:\path\to\yt-sptfy-exporter\app.py"
   ```

4. Name the shortcut and click Finish.

Pointing the shortcut at `pythonw.exe`, the windowed build of Python, means the app opens with no console window behind it. To set a custom icon or pin the app, right-click the shortcut and use Properties, Pin to Start, or Pin to taskbar.

## Running

From the project folder:

```sh
uv run app.py
```

On the first run, uv creates a virtual environment (`.venv`) and installs the dependencies automatically.

Paste a playlist or song URL, choose an output folder, and click Download.

No Spotify account or API credentials are required. Track metadata comes from the same public web-player API that the Spotify embed widget uses, so only public playlists and tracks work.

## YouTube rate-limiting

The app downloads one track at a time to stay under YouTube's limits for anonymous users. If you still see `HTTP Error 429`, that response is not counted as a failed track. The app pauses for a cooldown (`RATE_LIMIT_COOLDOWN` in `app.py`, 60 seconds by default) and then retries, so nothing is dropped just because YouTube throttled you. The log shows a `Pausing 60s...` message followed by `resuming`.
