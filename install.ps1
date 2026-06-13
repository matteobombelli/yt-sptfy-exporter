# Installs dependencies for yt-sptfy-exporter: uv, ffmpeg, deno (Windows)

function Install-IfMissing($Command, $WingetId, $Label) {
    if (Get-Command $Command -ErrorAction SilentlyContinue) {
        Write-Host "$Label already installed"
    } else {
        Write-Host "Installing $Label..."
        winget install --id $WingetId -e --accept-source-agreements --accept-package-agreements
    }
}

Install-IfMissing uv     astral-sh.uv  "uv"
Install-IfMissing ffmpeg Gyan.FFmpeg   "ffmpeg"
Install-IfMissing deno   DenoLand.Deno "deno (JS runtime used by yt-dlp)"

Write-Host ""
Write-Host "All dependencies installed. Restart your terminal, then run: uv run app.py"
