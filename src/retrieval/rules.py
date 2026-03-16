from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from src.core.models import PaperRecord


def _norm(s: str) -> str:
    """Lowercase + collapse whitespace for robust substring matching."""
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _match_keywords(text: str, keywords: List[str]) -> List[str]:
    """
    Simple substring match.
    Returns the list of keywords that appear in text (case-insensitive).
    """
    t = _norm(text)
    hits: List[str] = []
    for kw in keywords:
        kw_n = _norm(kw)
        if not kw_n:
            continue
        if kw_n in t:
            hits.append(kw)
    return hits


def _author_match(authors: List[str], aliases: List[str]) -> bool:
    """
    Match if any alias is a substring of any author string (case-insensitive).
    This is tolerant to formats like "Dai, Xi" or "X. Dai".
    """
    if not authors or not aliases:
        return False

    authors_n = [_norm(a) for a in authors]
    aliases_n = [_norm(x) for x in aliases if str(x).strip()]

    for a in authors_n:
        for al in aliases_n:
            if al and al in a:
                return True
    return False


def _collect_watch_aliases(rules_cfg: Dict[str, Any]) -> List[str]:
    """
    Collect aliases from rules.people.watch_authors[*].aliases.

    If you later implement aliases_ref loading in config.py,
    you can keep this function unchanged and just expand rules_cfg upstream.
    """
    people = (rules_cfg or {}).get("people", {}) or {}
    watch = people.get("watch_authors", []) or []
    aliases: List[str] = []
    for entry in watch:
        for al in (entry.get("aliases", []) or []):
            if isinstance(al, str) and al.strip():
                aliases.append(al.strip())
    return aliases


def apply_rule_filter(
    records: List[PaperRecord],
    rules_cfg: Dict[str, Any],
) -> Tuple[List[PaperRecord], List[PaperRecord]]:
    """
    Apply rule-based coarse filtering:
      - keyword hits from topics (include/exclude)
      - author watchlist match
      - compute rule_score
      - filter by min_rule_score

    Returns: (kept_records, dropped_records)
    """
    rules_cfg = rules_cfg or {}

    topics = rules_cfg.get("topics", []) or []
    scoring = rules_cfg.get("scoring", {}) or {}

    w_keyword = int(scoring.get("keyword_hit", 1))
    w_author = int(scoring.get("author_match", 5))
    w_excl = int(scoring.get("exclude_penalty", -3))

    min_score = int(rules_cfg.get("min_rule_score", 1))

    watch_aliases = _collect_watch_aliases(rules_cfg)

    kept: List[PaperRecord] = []
    dropped: List[PaperRecord] = []

    for r in records:
        text = f"{r.title}\n{r.abstract}"

        # ----- keyword hits + topic-once scoring -----
        include_hits_all: List[str] = []
        exclude_hits_all: List[str] = []

        score = 0

        for topic in topics:
            name = str(topic.get("name", "topic")).strip() or "topic"
            weight = int(topic.get("weight", 1))  # ✅ topic 固定分，默认 1

            includes = topic.get("include_keywords", []) or []
            excludes = topic.get("exclude_keywords", []) or []

            inc_hits = _match_keywords(text, [str(x) for x in includes])
            exc_hits = _match_keywords(text, [str(x) for x in excludes])

            # record hits with topic label for interpretability
            include_hits_all.extend([f"{name}:{h}" for h in inc_hits])
            exclude_hits_all.extend([f"{name}:-{h}" for h in exc_hits])

            # topic 命中只计一次分
            if len(inc_hits) > 0:
                score += weight

            # exclude 命中也只扣一次（不按命中数扣）
            if len(exc_hits) > 0:
                score += w_excl  # w_excl 例如 -3

        # optional: dedupe while preserving order
        def _dedupe(seq: List[str]) -> List[str]:
            seen = set()
            out = []
            for x in seq:
                if x not in seen:
                    out.append(x)
                    seen.add(x)
            return out

        include_hits_all = _dedupe(include_hits_all)
        exclude_hits_all = _dedupe(exclude_hits_all)

        # ----- author match -----
        a_match = _author_match(r.authors, watch_aliases)
        if a_match:
            score += w_author



        # ----- write back signals -----
        r.signals.keyword_hits = include_hits_all + exclude_hits_all
        r.signals.author_match = a_match
        r.signals.rule_score = int(score)

        # update timestamp if you want; safe to leave to other modules
        # r.updated_at = datetime.utcnow()

        if score >= min_score:
            kept.append(r)
        else:
            dropped.append(r)

    # Sort kept by score descending as a useful default
    kept.sort(key=lambda x: x.signals.rule_score, reverse=True)

    return kept, dropped
