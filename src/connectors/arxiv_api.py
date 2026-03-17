from __future__ import annotations

import time as _time
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import feedparser
import requests

from src.core.models import PaperRecord, Assets


ARXIV_API = "https://export.arxiv.org/api/query"


# -----------------------------
# Time window helpers
# -----------------------------
def _normalize_time_window(time_window: Dict[str, Any]) -> Tuple[str, int]:
    """
    time_window example:
      {"unit": "hours", "value": 24}
      {"unit": "days", "value": 30}
      {"unit": "weeks", "value": 2}
      {"unit": "months", "value": 1}  # approx as 30 days
      {"unit": "years", "value": 10}  # approx as 365 days

    Returns: (unit, value)
    """
    if not isinstance(time_window, dict):
        raise ValueError("time_window must be a dict like {'unit':'hours','value':24}")

    unit = str(time_window.get("unit", "hours")).strip().lower()
    value = time_window.get("value", 24)

    try:
        value_int = int(value)
    except Exception as e:
        raise ValueError(f"time_window.value must be int-like, got {value!r}") from e

    if value_int <= 0:
        raise ValueError(f"time_window.value must be > 0, got {value_int}")

    return unit, value_int

def _compute_day_aligned_window(
    now_utc: datetime,
    *,
    days: int = 1,
) -> tuple[datetime, datetime]:
    """
    返回 [start, end) 的 UTC 时间窗口
    例：days=1 → 昨天 00:00 到 今天 00:00
    """
    today_0 = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    start = today_0 - timedelta(days=days)
    end = today_0
    return start, end


def _compute_cutoff(now_utc: datetime, time_window: Dict[str, Any]) -> datetime:
    unit, value = _normalize_time_window(time_window)

    if unit in ("hour", "hours", "h"):
        delta = timedelta(hours=value)
    elif unit in ("day", "days", "d"):
        delta = timedelta(days=value)
    elif unit in ("week", "weeks", "w"):
        delta = timedelta(weeks=value)
    elif unit in ("month", "months", "m"):
        # arXiv 这种用途用近似就足够：1 month ≈ 30 days
        delta = timedelta(days=30 * value)
    elif unit in ("year", "years", "y"):
        delta = timedelta(days=365 * value)
    else:
        raise ValueError(f"Unsupported time_window unit: {unit}")

    return now_utc - delta


# -----------------------------
# Atom parsing helpers
# -----------------------------
def _struct_time_to_dt_utc(st: Optional[_time.struct_time]) -> Optional[datetime]:
    if st is None:
        return None
    return datetime(
        st.tm_year, st.tm_mon, st.tm_mday,
        st.tm_hour, st.tm_min, st.tm_sec,
        tzinfo=timezone.utc,
    )


def _pick_pdf_url(entry) -> str:
    for link in getattr(entry, "links", []) or []:
        if getattr(link, "type", "") == "application/pdf":
            return link.href
    arxiv_id = entry.id.split("/abs/")[-1]
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


def _build_query(categories: List[str]) -> str:
    """
    Build arXiv search_query for categories.
    Example: (cat:cond-mat.str-el OR cat:physics.optics)
    """
    if not categories:
        raise ValueError("categories must be a non-empty list")
    cats = " OR ".join([f"cat:{c}" for c in categories])
    return f"({cats})"


def _get_arxiv_response_text(
    url: str,
    *,
    headers: dict[str, str],
    timeout_s: int,
    max_attempts: int = 4,
    base_sleep_s: float = 2.0,
) -> str:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout_s)
            resp.raise_for_status()
            return resp.text
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            sleep_s = base_sleep_s * (2 ** (attempt - 1))
            print(
                f"[RETRY] arXiv request failed ({type(exc).__name__}) "
                f"attempt {attempt}/{max_attempts}, sleep={sleep_s:.1f}s"
            )
            _time.sleep(sleep_s)
    assert last_error is not None
    raise last_error


# -----------------------------
# Public API
# -----------------------------
def fetch_arxiv(
    categories: List[str],
    time_window: Dict[str, Any],
    max_results: int = 200,
    *,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
    user_agent: str = "paper-scout/0.1 (contact: your-email-or-github)",
    timeout_s: int = 60,
    polite_delay_s: float = 0.0,
) -> List[PaperRecord]:
    """
    Fetch arXiv entries by categories, then strictly filter by time_window.

    Notes:
    - arXiv API is a search API; it doesn't support "after=timestamp" directly.
    - We fetch recent results sorted by submittedDate descending, then filter locally.
    - For very large windows (e.g. 10 years), arXiv OAI-PMH is more appropriate,
      but this function remains useful for daily/weekly/monthly windows.
    """
    now_utc = datetime.now(timezone.utc)

    unit, value = _normalize_time_window(time_window)

    cutoff = _compute_cutoff(now_utc, time_window)
    window_start, window_end = cutoff, now_utc


    query = _build_query(categories)
    params = {
        "search_query": query,
        "start": 0,
        "max_results": int(max_results),
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    url = ARXIV_API + "?" + urllib.parse.urlencode(params)

    headers = {"User-Agent": user_agent}

    feed_text = _get_arxiv_response_text(url, headers=headers, timeout_s=timeout_s)
    feed = feedparser.parse(feed_text)

    records: List[PaperRecord] = []
    for e in feed.entries:
        arxiv_id = e.id.split("/abs/")[-1]

        title = " ".join(getattr(e, "title", "").split())
        abstract = " ".join(getattr(e, "summary", "").split())

        authors = [a.name for a in getattr(e, "authors", [])] if getattr(e, "authors", None) else []
        cats = [t.term for t in getattr(e, "tags", [])] if getattr(e, "tags", None) else []

        published_dt = _struct_time_to_dt_utc(getattr(e, "published_parsed", None))
        updated_dt = _struct_time_to_dt_utc(getattr(e, "updated_parsed", None))

        # 用 updated 优先（更符合“最近变动”）；没有就用 published
        ts = updated_dt or published_dt
        if ts is None:
            continue

        # 严格时间窗口过滤
        if not (window_start <= ts < window_end):
            continue

        pdf_url = _pick_pdf_url(e)

        rec = PaperRecord(
            id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            categories=cats,
            published=published_dt or ts,
            updated=updated_dt,
            source="arxiv",
            mode="daily",
            assets=Assets(pdf_url=pdf_url),
            updated_at=datetime.now(timezone.utc),
        )
        records.append(rec)

        if polite_delay_s > 0:
            _time.sleep(polite_delay_s)

    return records
