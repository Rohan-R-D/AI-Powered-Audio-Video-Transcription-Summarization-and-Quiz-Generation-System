import os
import shutil
import tempfile

import yt_dlp


def download_youtube_media(url: str, prefer_audio: bool = True) -> str:
    """Download a YouTube video/audio and return the local file path.

    If prefer_audio is True, tries to fetch best audio; otherwise best mp4.
    """
    tmpdir = tempfile.mkdtemp()
    outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")
    ydl_opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "noprogress": True,
    }
    node_path = shutil.which("node")
    if node_path:
        ydl_opts["js_runtimes"] = {"node": {"path": node_path}}

    if prefer_audio:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": "192",
                }
            ],
        })
    else:
        ydl_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "merge_output_format": "mp4",
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "requested_downloads" in info and info["requested_downloads"]:
            # Newer yt-dlp returns requested downloads
            path = info["requested_downloads"][0]["filepath"]
        else:
            path = ydl.prepare_filename(info)
            # Postprocessor may have changed extension
            if prefer_audio:
                base, _ = os.path.splitext(path)
                candidate = base + ".m4a"
                if os.path.exists(candidate):
                    path = candidate
        return path

