from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.models import PaperRecord


def _fmt_date(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    # Keep only date for readability
    return dt.date().isoformat()


def _md_escape(s: str) -> str:
    # minimal escaping; keep it simple for now
    return s.replace("\r\n", "\n").replace("\r", "\n").strip()


def _authors_line(authors: List[str]) -> str:
    return ", ".join([a.strip() for a in authors if a and a.strip()])


def _block_quote(text: str) -> str:
    """
    Render full abstract as markdown quote block.
    """
    text = _md_escape(text)
    if not text:
        return "> (no abstract)\n"
    lines = text.split("\n")
    return "\n".join([f"> {ln}".rstrip() for ln in lines]) + "\n"


@dataclass
class ReportMeta:
    date: str
    profile_name: str
    mode_name: str
    fetched: int
    kept: int
    dropped: int


def write_daily_markdown_report(
    out_path: str | Path,
    records_ranked: List[PaperRecord],
    meta: ReportMeta,
    *,
    include_rule_signals: bool = True,
) -> Path:
    """
    Write a markdown daily report.

    Display priority per paper:
      1) Title
      2) Authors (all)
      3) Abstract (full)
      4) PDF link
      then:
      - arXiv id
      - categories
      - published/updated
      - rule_score / keyword_hits / author_match (optional)
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append(f"# Daily arXiv Digest")
    lines.append("")
    lines.append(f"- Date: {meta.date}")
    lines.append(f"- Profile: {meta.profile_name}")
    lines.append(f"- Mode: {meta.mode_name}")
    lines.append(f"- Fetched: {meta.fetched}")
    lines.append(f"- Kept (after rules): {meta.kept}")
    lines.append(f"- Dropped: {meta.dropped}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not records_ranked:
        lines.append("_No papers matched the current rules._")
        lines.append("")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    # Ensure already sorted by "relevance" (rule_score) descending
    for idx, r in enumerate(records_ranked, start=1):
        title = _md_escape(r.title)
        authors = _authors_line(r.authors)
        abstract = r.abstract or ""
        pdf_url = getattr(r.assets, "pdf_url", "") if r.assets else ""
        arxiv_id = r.id

        lines.append(f"## Rank #{idx}")
        lines.append("")
        # 1) Title
        lines.append(f"**Title:** {title}")
        lines.append("")
        # NEW: Keyword hits right after title
        if include_rule_signals and getattr(r, "signals", None) is not None:
            hits = getattr(r.signals, "keyword_hits", []) or []
            if hits:
                lines.append(f"**Keyword hits:** {', '.join(hits)}")
                lines.append("")
        # 2) Authors
        lines.append(f"**Authors:** {authors if authors else '(unknown)'}")
        lines.append("")
        
        lines.append(f"**Author_match:** {bool(getattr(r.signals, 'author_match', False))}")
        lines.append("")
        
        # 3) Abstract (full)
        lines.append("**Abstract:**")
        lines.append(_block_quote(abstract).rstrip())
        lines.append("")
        # 4) PDF
        if pdf_url:
            lines.append(f"**PDF:** {pdf_url}")
        else:
            lines.append("**PDF:** (missing)")
        lines.append("")

        # Other fields (less important)
        lines.append("**Details:**")
        lines.append(f"- arXiv: {arxiv_id}")
        if r.categories:
            lines.append(f"- Categories: {', '.join(r.categories)}")
        pub = _fmt_date(getattr(r, "published", None))
        upd = _fmt_date(getattr(r, "updated", None))
        if pub:
            lines.append(f"- Published: {pub}")
        if upd and upd != pub:
            lines.append(f"- Updated: {upd}")

        if include_rule_signals and getattr(r, "signals", None) is not None:
            lines.append(f"- rule_score: {r.signals.rule_score}")

        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
