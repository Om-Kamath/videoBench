"""
videoBench Sync
---------------
Pull the latest videos from the shared Hugging Face dataset.

Usage:
    python sync.py               # download everything
    python sync.py CaseyNeistat  # download a specific channel only

Requirements:
    pip install huggingface_hub
"""

import sys
import os
from huggingface_hub import snapshot_download

HF_REPO_ID = "omkamath/videoBench"
LOCAL_DIR = "downloaded_vlogs"


def main():
    channel = sys.argv[1] if len(sys.argv) > 1 else None

    print("\n" + "=" * 50)
    print("  videoBench Sync")
    print("=" * 50)

    if channel:
        print(f"\nSyncing channel: {channel}")
        patterns = [f"{channel}/*"]
    else:
        print("\nSyncing all channels...")
        patterns = None

    snapshot_download(
        repo_id=HF_REPO_ID,
        repo_type="dataset",
        local_dir=LOCAL_DIR,
        allow_patterns=patterns,
    )

    print(f"\n  Synced to ./{LOCAL_DIR}/")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
