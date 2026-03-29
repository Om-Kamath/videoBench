"""
YouTube Vlog Downloader
-----------------------
Downloads up to 5 videos from a YouTube channel.
Targets vlog-style content by filtering for mid-length videos (3-30 min).

Usage:
    python download_vlogs.py

Requirements:
    pip install yt-dlp
"""

import yt_dlp
import os
import sys
from huggingface_hub import HfApi

HF_REPO_ID = "omkamath/videoBench"


def get_channel_url():
    """Prompt user for the YouTube channel URL."""
    print("\n" + "=" * 50)
    print("  YouTube Vlog Downloader")
    print("=" * 50)
    url = input("\nPaste the YouTube channel URL:\n> ").strip()

    # Normalize the URL to point to the videos tab
    if not url:
        print("No URL provided. Exiting.")
        sys.exit(1)

    # Handle various channel URL formats
    for suffix in ["/videos", "/shorts", "/streams", "/playlists", "/about"]:
        if url.endswith(suffix):
            url = url.removesuffix(suffix)
            break
    url = url.rstrip("/")

    return url + "/videos"


def download_vlogs(channel_url, output_dir="downloaded_vlogs", max_videos=5):
    """
    Download vlog-style videos from a YouTube channel.

    Args:
        channel_url: Full URL to the channel's /videos page.
        output_dir:  Folder to save downloads into.
        max_videos:  How many videos to download (default 5).
    """
    os.makedirs(output_dir, exist_ok=True)

    # --- Step 1: Scan the channel for vlog-length videos (3–30 min) ---
    print(f"\nScanning channel for vlog-length videos (3–30 minutes)...")

    scan_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "playlistend": 50,           # scan more to find enough chaptered videos
        "ignoreerrors": True,
        "match_filter": "duration >= 180 & duration <= 1800",  # 3–30 min
    }

    with yt_dlp.YoutubeDL(scan_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    if not info or "entries" not in info:
        print("Could not retrieve videos. Check the URL and try again.")
        return

    # Filter out None entries and videos without chapter markers
    videos = [v for v in info["entries"] if v is not None and v.get("chapters")]

    if not videos:
        print("No vlog-length videos with chapter markers found on this channel.")
        return

    # Take only the number we want
    videos = videos[:max_videos]

    print(f"\nFound {len(videos)} video(s) with chapter markers to download:\n")
    for i, v in enumerate(videos, 1):
        mins = v.get("duration", 0) // 60
        secs = v.get("duration", 0) % 60
        print(f"  {i}. {v.get('title', 'Unknown')}  ({mins}:{secs:02d})")

    # --- Step 2: Download the selected videos ---
    # Output structure: output_dir/<channel>/<date> - <title>/<date> - <title>.mp4
    print(f"\nDownloading to ./{output_dir}/\n")

    video_folder_tmpl = os.path.join(
        output_dir,
        "%(channel)s",
        "%(upload_date)s - %(title)s",
        "%(upload_date)s - %(title)s.%(ext)s",
    )

    download_opts = {
        "format": "bestvideo[height<=480]+bestaudio/best",
        "outtmpl": video_folder_tmpl,
        "merge_output_format": "mp4",
        "writethumbnail": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "writedescription": True,   # saves <title>.description in the video folder
        "writeinfojson": True,      # saves <title>.info.json with full metadata
        "subtitleslangs": ["en"],
        "ignoreerrors": True,
        "progress_hooks": [progress_hook],
        "postprocessors": [
            {"key": "EmbedThumbnail"},
        ],
    }

    channel_name = videos[0].get("channel", "Unknown")

    with yt_dlp.YoutubeDL(download_opts) as ydl:
        urls = [v["webpage_url"] for v in videos]
        ydl.download(urls)

    print("\n" + "=" * 50)
    print(f"  Done! {len(videos)} video(s) saved to ./{output_dir}/")
    print(f"  Each video has its own folder with .description and .info.json")
    print("=" * 50 + "\n")

    # --- Step 3: Upload the channel folder to Hugging Face ---
    upload_to_hub(channel_name, output_dir)


def upload_to_hub(channel_name, output_dir):
    """Upload the channel folder to the Hugging Face dataset repo."""
    channel_dir = os.path.join(output_dir, channel_name)
    if not os.path.isdir(channel_dir):
        print(f"  Warning: could not find {channel_dir} to upload.")
        return

    print(f"\nUploading '{channel_name}' to Hugging Face ({HF_REPO_ID})...")
    api = HfApi()
    api.upload_folder(
        folder_path=channel_dir,
        repo_id=HF_REPO_ID,
        repo_type="dataset",
        path_in_repo=channel_name,
        commit_message=f"Add videos from {channel_name}",
    )
    print(f"  Done: https://huggingface.co/datasets/{HF_REPO_ID}\n")


def progress_hook(d):
    """Print a simple progress indicator."""
    if d["status"] == "downloading":
        pct = d.get("_percent_str", "??%").strip()
        speed = d.get("_speed_str", "").strip()
        print(f"\r  Downloading: {pct}  {speed}  ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r  Download complete, processing...           ")


if __name__ == "__main__":
    channel = get_channel_url()
    download_vlogs(channel)