# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run the app:** `uv run app.py` (creates `.venv/` and installs deps on first run)
- **Install system deps:** `./install.sh` (macOS/Linux) or `powershell -ExecutionPolicy Bypass -File install.ps1` (Windows). Installs uv, **ffmpeg**, and **deno**.
- **Lint:** `uvx ruff check app.py` (a `.ruff_cache/` exists; ruff is the linter in use)

There is no test suite. The app is a single-file Tkinter GUI, so changes are verified by running it.

### Runtime dependencies (must be on PATH, not just pip-installed)
- **ffmpeg** — all audio transcode/copy and metadata/cover tagging shells out to it.
- **deno** — yt-dlp fetches a JS challenge solver (`remote_components: ["ejs:github"]`) that runs on deno; required for full YouTube format access.

## Architecture

Everything lives in `app.py` (~790 lines), structured top-to-bottom in labeled sections. The flow is **URL → metadata → match → download → tag**, with the GUI dispatching background jobs that report progress over a queue.

### Spotify without credentials (key design choice)
Spotify's official Web API requires OAuth and 403s for new apps, so metadata is read the way the public web player does:
1. `_embed_state()` scrapes the `__NEXT_DATA__` JSON from `open.spotify.com/embed/...`, which carries an anonymous access token.
2. `_pathfinder_tracks()` uses that token against the web-player GraphQL ("pathfinder") API (`FETCH_PLAYLIST_HASH` is a persisted-query hash) with offset pagination, so playlists of any length work.
3. On failure it falls back to the embed page's inline track list (max 100, no album info).

Only **public** playlists/tracks work. Spotify tracks have no audio — each is resolved to a YouTube video by search.

### Matching (Spotify → YouTube)
`find_match()` runs a `ytsearchN:` query, then scores candidates with `match_score()`: order-invariant word-set similarity of `"artist title"` vs the video title (and title+channel, to catch "Artist - Topic"/VEVO uploads), minus a penalty for duration mismatch. `version_allowed()` pre-filters by studio/live preference. Only matches at/above the user's strictness threshold are downloaded; everything else is reported as skipped. `MIN_SOURCE_KBPS` drops sources whose best audio bitrate is below the floor (degraded uploads).

### Download & tagging
`download_audio()` handles four quality modes: `128`/`192` transcode to MP3 (lossy); `opus`/`m4a` keep YouTube's native stream losslessly. Tagging branches by format: Opus is tagged via **mutagen** (ffmpeg's Ogg muxer can't write covers), MP3/M4A via an ffmpeg `-c copy` remux that retries metadata-only if cover embedding fails.

### Rate-limiting
Jobs (`run_spotify_job`, `run_youtube_job`) process tracks **one at a time** in a plain sequential loop — single-worker by design, to stay under YouTube's anonymous rate limits. `run_with_retry()` wraps every network call: on a YouTube 429 it logs, sleeps `RATE_LIMIT_COOLDOWN`, and retries up to `MAX_RATE_LIMIT_RETRIES`; any other error (including a 403) propagates to the per-track `except`, which logs it and moves to the next track — nothing else is retried.

### GUI ↔ worker communication
`App` (Tkinter) starts the job on a daemon thread; the worker never touches widgets directly — it pushes `("log"|"progress"|"done", ...)` tuples onto `self.q`, drained by `_poll()` on the Tk main loop via `root.after`.

### Tuning knobs (module-level constants, top of `app.py`)
`DEFAULT_STRICTNESS`, `DURATION_TOLERANCE`, `MIN_SOURCE_KBPS`, `SEARCH_RESULTS`, `RATE_LIMIT_COOLDOWN`, `MAX_RATE_LIMIT_RETRIES`.

---

Always signoff your responses with "What do you think, Matteo?"

Follow the Karpathy Guidelines

1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

    State your assumptions explicitly. If uncertain, ask.
    If multiple interpretations exist, present them - don't pick silently.
    If a simpler approach exists, say so. Push back when warranted.
    If something is unclear, stop. Name what's confusing. Ask.

2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

    No features beyond what was asked.
    No abstractions for single-use code.
    No "flexibility" or "configurability" that wasn't requested.
    No error handling for impossible scenarios.
    If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.
3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:

    Don't "improve" adjacent code, comments, or formatting.
    Don't refactor things that aren't broken.
    Match existing style, even if you'd do it differently.
    If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

    Remove imports/variables/functions that YOUR changes made unused.
    Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.
4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:

    "Add validation" → "Write tests for invalid inputs, then make them pass"
    "Fix the bug" → "Write a test that reproduces it, then make it pass"
    "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
