from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Iterable, Optional

import requests

from src.core.models import PaperRecord


# -----------------------------
# Utilities
# -----------------------------

INVALID_CHARS = r'[\\/:*?"<>|]'


def sanitize_filename(name: str, max_len: int = 120) -> str:
    """
    Make a filename safe for Windows/macOS/Linux.
    """
    name = name.strip()
    name = re.sub(INVALID_CHARS, "", name)
    name = re.sub(r"\s+", " ", name)
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name


# -----------------------------
# Core downloader
# -----------------------------

def download_pdf(
    url: str,
    out_path: Path,
    *,
    timeout: int = 30,
) -> None:
    """
    Download a PDF from url to out_path.
    """
    headers = {
        "User-Agent": "paper-scout/0.1 (+arXiv crawler for personal research)"
    }

    with requests.get(url, headers=headers, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def download_papers(
    records: Iterable[PaperRecord],
    out_dir: str | Path,
    *,
    sleep_s: float = 1.0,
    overwrite: bool = False,
) -> list[Path]:
    """
    Download PDFs for a list of PaperRecord.

    Filenames:
      <score>_<sanitized_title>__<arxiv_id>.pdf

    Returns:
      List of downloaded file paths.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[Path] = []

    for r in records:
        if not r.assets or not r.assets.pdf_url:
            continue

        title = sanitize_filename(r.title)
        arxiv_id = r.id.replace("/", "_")

        filename = f"{r.signals.rule_score}_{title}__{arxiv_id}.pdf"
        out_path = out_dir / filename

        if out_path.exists() and not overwrite:
            downloaded.append(out_path)
            continue

        try:
            print(f"⬇ Downloading: {r.title}")
            download_pdf(r.assets.pdf_url, out_path)
            downloaded.append(out_path)
            time.sleep(sleep_s)
        except Exception as e:
            print(f"⚠ Failed to download {r.id}: {e}")

    return downloaded
