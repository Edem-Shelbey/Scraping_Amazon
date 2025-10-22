import os
import html
import re
import time
import random
from typing import Optional


def safe_filename(s: str, max_len: int = 120) -> str:
    if not s:
        return "unnamed"
    s = html.unescape(s)
    s = re.sub(r"[\\/:*?\"<>|\n\r\t]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ _\-\.,]", "", s)
    s = s.replace(" ", "_")
    if len(s) > max_len:
        s = s[:max_len].rstrip("_")
    return s or "unnamed"


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def jitter_sleep(a: float = 0.2, b: float = 0.8):
    """Sleep a bit between requests to avoid looking too bot-like."""
    time.sleep(random.uniform(a, b))