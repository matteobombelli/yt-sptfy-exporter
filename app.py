"""Playlist -> MP3 downloader.

Paste a Spotify or YouTube playlist URL, pick a folder, get MP3s.
Spotify playlists are resolved track-by-track via YouTube search.
"""

import base64
import difflib
import json
import os
import queue
import re
import shutil
import subprocess
import threading
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import yt_dlp

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
MATCH_THRESHOLD = 0.6
DURATION_TOLERANCE = 15  # seconds
ACCENT = "#1DB954"


# ---------- config ----------

def load_config():
    if not CONFIG_PATH.exists():
        save_config({"spotify_client_id": "", "spotify_client_secret": ""})
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# ---------- spotify ----------

def spotify_token(client_id, client_secret):
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        headers={"Authorization": f"Basic {auth}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["access_token"]


def spotify_tracks(token, playlist_id):
    url = (f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
           "?limit=100&fields=next,items(track(name,duration_ms,artists(name),album(name)))")
    tracks = []
    while url:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
        for item in data["items"]:
            t = item.get("track")
            if t and t.get("name"):
                tracks.append({
                    "artist": t["artists"][0]["name"] if t["artists"] else "",
                    "title": t["name"],
                    "album": (t.get("album") or {}).get("name", ""),
                    "duration": (t.get("duration_ms") or 0) / 1000,
                })
        url = data.get("next")
    return tracks


# Fallback for when Spotify blocks the playlist-tracks endpoint (403, the case
# for newly created API apps): the public embed page carries an anonymous
# web-player token, which the web player's GraphQL API accepts - including
# offset pagination, so playlists of any length work.

PATHFINDER_URL = "https://api-partner.spotify.com/pathfinder/v1/query"
FETCH_PLAYLIST_HASH = "b39f62e9b566aa849b1780927de1450f47e02c54abf1e66e513f96e849591e41"


def _embed_state(playlist_id):
    req = urllib.request.Request(
        f"https://open.spotify.com/embed/playlist/{playlist_id}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode()
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise RuntimeError("Could not read playlist from Spotify embed page")
    return json.loads(m.group(1))["props"]["pageProps"]["state"]


def _pathfinder_tracks(playlist_id, token):
    tracks, offset, total = [], 0, None
    while total is None or offset < total:
        params = urllib.parse.urlencode({
            "operationName": "fetchPlaylist",
            "variables": json.dumps(
                {"uri": f"spotify:playlist:{playlist_id}", "offset": offset, "limit": 100}),
            "extensions": json.dumps(
                {"persistedQuery": {"version": 1, "sha256Hash": FETCH_PLAYLIST_HASH}}),
        })
        req = urllib.request.Request(
            f"{PATHFINDER_URL}?{params}",
            headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req) as resp:
            content = json.load(resp)["data"]["playlistV2"]["content"]
        total = content["totalCount"]
        for item in content["items"]:
            data = (item.get("itemV2") or {}).get("data") or {}
            if data.get("__typename") != "Track" or not data.get("name"):
                continue
            artists = [a["profile"]["name"] for a in data["artists"]["items"]]
            tracks.append({
                "artist": artists[0] if artists else "",
                "title": data["name"],
                "album": (data.get("albumOfTrack") or {}).get("name", ""),
                "duration": data["trackDuration"]["totalMilliseconds"] / 1000,
            })
        offset += 100
    return tracks


def spotify_tracks_noauth(playlist_id, log):
    state = _embed_state(playlist_id)
    try:
        return _pathfinder_tracks(playlist_id, state["settings"]["session"]["accessToken"])
    except Exception as e:
        log(f"Web-player API failed ({e}) - using embed track list (max 100 tracks, no album info).")
        return [{
            "artist": t.get("subtitle") or "",
            "title": t["title"],
            "album": "",
            "duration": (t.get("duration") or 0) / 1000,
        } for t in state["data"]["entity"]["trackList"]]


# ---------- youtube matching ----------

BRACKETS = re.compile(r"\(.*?\)|\[.*?\]")
NOISE_WORDS = re.compile(r"\b(official|video|audio|lyrics?|music|hd|4k|remaster(ed)?)\b")


def normalize(s):
    s = BRACKETS.sub(" ", s.lower())
    s = NOISE_WORDS.sub(" ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def match_score(track, entry):
    want = normalize(f"{track['artist']} {track['title']}")
    got = normalize(entry.get("title") or "")
    score = difflib.SequenceMatcher(None, want, got).ratio()
    duration = entry.get("duration")
    if track["duration"] and duration and abs(duration - track["duration"]) > DURATION_TOLERANCE:
        score -= 0.2
    return score


def find_youtube_match(track, search_ydl):
    query = f"{track['artist']} {track['title']}"
    info = search_ydl.extract_info(f"ytsearch5:{query}", download=False)
    best, best_score = None, 0.0
    for entry in info.get("entries") or []:
        score = match_score(track, entry)
        if score > best_score:
            best, best_score = entry, score
    if best and best_score >= MATCH_THRESHOLD:
        return best["url"], best_score
    return None, best_score


# ---------- download ----------

def sanitize(name):
    return re.sub(r'[\\/:*?"<>|%]', "_", name).strip()


def unique_base(outdir, name):
    """Path (without extension) for name.mp3, adding (2), (3)... on collision."""
    base = Path(outdir) / name
    n = 2
    while base.with_suffix(".mp3").exists():
        base = Path(outdir) / f"{name} ({n})"
        n += 1
    return str(base)


def download_mp3(url, out_path_no_ext, meta=None):
    opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{out_path_no_ext}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noprogress": True,
        # let yt-dlp fetch its JS challenge solver (runs on deno), needed for
        # full YouTube format access
        "remote_components": ["ejs:github"],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    if meta:
        mp3 = f"{out_path_no_ext}.mp3"
        tagged = f"{out_path_no_ext}.tagged.mp3"
        cmd = ["ffmpeg", "-y", "-i", mp3, "-c", "copy"]
        for key, value in meta.items():
            if value:
                cmd += ["-metadata", f"{key}={value}"]
        cmd.append(tagged)
        subprocess.run(cmd, check=True, capture_output=True)
        os.replace(tagged, mp3)


# ---------- worker jobs (run in a thread, report via queue) ----------

def run_spotify_job(url, outdir, cfg, q):
    playlist_id = re.search(r"playlist/([A-Za-z0-9]+)", url).group(1)
    q.put(("log", "Fetching Spotify playlist metadata..."))
    try:
        token = spotify_token(cfg["spotify_client_id"], cfg["spotify_client_secret"])
        tracks = spotify_tracks(token, playlist_id)
    except urllib.error.HTTPError as e:
        if e.code != 403:
            raise
        q.put(("log", "Spotify API denied playlist access (new API apps are restricted) - "
                      "falling back to the public web-player API."))
        tracks = spotify_tracks_noauth(playlist_id, lambda msg: q.put(("log", msg)))
    q.put(("log", f"Found {len(tracks)} tracks. Searching YouTube..."))
    q.put(("progress", 0, len(tracks)))

    search_ydl = yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True, "noprogress": True})
    skipped = []
    for i, track in enumerate(tracks, 1):
        label = f"{track['artist']} - {track['title']}"
        try:
            video_url, score = find_youtube_match(track, search_ydl)
            if not video_url:
                skipped.append(label)
                q.put(("log", f"[{i}/{len(tracks)}] Skipped (no confident match, best {score:.2f}): {label}"))
            else:
                q.put(("log", f"[{i}/{len(tracks)}] Downloading (match {score:.2f}): {label}"))
                download_mp3(video_url, unique_base(outdir, sanitize(track["title"])), meta={
                    "title": track["title"],
                    "artist": track["artist"],
                    "album": track.get("album", ""),
                })
        except Exception as e:
            skipped.append(label)
            q.put(("log", f"[{i}/{len(tracks)}] Failed: {label} ({e})"))
        q.put(("progress", i, len(tracks)))

    summary = f"Done: {len(tracks) - len(skipped)} downloaded, {len(skipped)} skipped."
    if skipped:
        summary += "\nSkipped tracks:\n  " + "\n  ".join(skipped)
    q.put(("done", summary))


def run_youtube_job(url, outdir, q):
    q.put(("log", "Fetching YouTube playlist..."))
    with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True, "noprogress": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = [e for e in (info.get("entries") if "entries" in info else [info]) if e]
    q.put(("log", f"Found {len(entries)} videos."))
    q.put(("progress", 0, len(entries)))

    failed = []
    for i, entry in enumerate(entries, 1):
        title = entry.get("title") or entry.get("id", "unknown")
        try:
            q.put(("log", f"[{i}/{len(entries)}] Downloading: {title}"))
            video_url = entry.get("url") or entry.get("webpage_url")
            download_mp3(video_url, unique_base(outdir, sanitize(title)))
        except Exception as e:
            failed.append(title)
            q.put(("log", f"[{i}/{len(entries)}] Failed: {title} ({e})"))
        q.put(("progress", i, len(entries)))

    summary = f"Done: {len(entries) - len(failed)} downloaded, {len(failed)} failed."
    if failed:
        summary += "\nFailed videos:\n  " + "\n  ".join(failed)
    q.put(("done", summary))


# ---------- UI ----------

class CredentialsDialog:
    """Modal dialog asking for Spotify Client ID / Secret. Saves to config.json."""

    def __init__(self, parent, cfg):
        self.cfg = cfg
        self.saved = False
        dlg = self.dlg = tk.Toplevel(parent)
        dlg.title("Spotify API credentials")
        dlg.resizable(False, False)
        dlg.transient(parent)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Enter your Spotify API credentials\n(see README for how to get them):").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.id_var = tk.StringVar(value=cfg.get("spotify_client_id", ""))
        self.secret_var = tk.StringVar(value=cfg.get("spotify_client_secret", ""))
        ttk.Label(frame, text="Client ID:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(frame, textvariable=self.id_var, width=40).grid(row=1, column=1, pady=2)
        ttk.Label(frame, text="Client Secret:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(frame, textvariable=self.secret_var, width=40, show="*").grid(row=2, column=1, pady=2)

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(buttons, text="Save", command=self._save).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=dlg.destroy).pack(side="left", padx=4)
        dlg.wait_window()

    def _save(self):
        cid, secret = self.id_var.get().strip(), self.secret_var.get().strip()
        if not cid or not secret:
            messagebox.showerror("Missing fields", "Both Client ID and Client Secret are required.", parent=self.dlg)
            return
        self.cfg["spotify_client_id"] = cid
        self.cfg["spotify_client_secret"] = secret
        save_config(self.cfg)
        self.saved = True
        self.dlg.destroy()


class App:
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self.q = queue.Queue()

        root.title("Playlist → MP3")
        root.geometry("700x520")
        root.minsize(560, 400)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Accent.TButton", background=ACCENT, foreground="white",
                        font=("TkDefaultFont", 10, "bold"), padding=8)
        style.map("Accent.TButton", background=[("active", "#1aa34a"), ("disabled", "#9bd6b0")])

        main = ttk.Frame(root, padding=16)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(4, weight=1)

        ttk.Label(main, text="Playlist URL (Spotify or YouTube):").grid(row=0, column=0, columnspan=3, sticky="w")
        self.url_var = tk.StringVar()
        ttk.Entry(main, textvariable=self.url_var).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 10))

        ttk.Label(main, text="Output folder:").grid(row=2, column=0, sticky="w")
        self.folder_var = tk.StringVar()
        ttk.Entry(main, textvariable=self.folder_var).grid(row=2, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(main, text="Browse…", command=self._browse).grid(row=2, column=2)

        self.download_btn = ttk.Button(main, text="Download", style="Accent.TButton", command=self._start)
        self.download_btn.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(12, 8))

        self.log = tk.Text(main, height=12, state="disabled", wrap="word",
                           relief="flat", background="#f5f5f5")
        self.log.grid(row=4, column=0, columnspan=3, sticky="nsew")
        scroll = ttk.Scrollbar(main, command=self.log.yview)
        scroll.grid(row=4, column=3, sticky="ns")
        self.log["yscrollcommand"] = scroll.set

        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        if not shutil.which("ffmpeg"):
            self._log("WARNING: ffmpeg not found on PATH - MP3 conversion will fail. See README.")

        root.after(100, self._poll)

    def _browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def _log(self, msg):
        self.log["state"] = "normal"
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log["state"] = "disabled"

    def _start(self):
        url = self.url_var.get().strip()
        outdir = self.folder_var.get().strip()
        if "open.spotify.com" in url and re.search(r"playlist/([A-Za-z0-9]+)", url):
            kind = "spotify"
        elif "youtube.com" in url or "youtu.be" in url:
            kind = "youtube"
        else:
            messagebox.showerror("Invalid URL", "Enter a Spotify playlist URL or a YouTube URL.")
            return
        if not outdir or not Path(outdir).is_dir():
            messagebox.showerror("No output folder", "Choose an existing output folder.")
            return
        if kind == "spotify" and not (self.cfg.get("spotify_client_id") and self.cfg.get("spotify_client_secret")):
            if not CredentialsDialog(self.root, self.cfg).saved:
                return

        self.download_btn["state"] = "disabled"
        self.progress["value"] = 0
        if kind == "spotify":
            target = run_spotify_job
            args = (url, outdir, self.cfg, self.q)
        else:
            target = run_youtube_job
            args = (url, outdir, self.q)
        threading.Thread(target=self._guarded, args=(target, args), daemon=True).start()

    def _guarded(self, target, args):
        try:
            target(*args)
        except Exception as e:
            self.q.put(("done", f"Error: {e}"))

    def _poll(self):
        try:
            while True:
                event = self.q.get_nowait()
                if event[0] == "log":
                    self._log(event[1])
                elif event[0] == "progress":
                    _, current, total = event
                    self.progress["maximum"] = max(total, 1)
                    self.progress["value"] = current
                elif event[0] == "done":
                    self._log(event[1])
                    self.download_btn["state"] = "normal"
        except queue.Empty:
            pass
        self.root.after(100, self._poll)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
