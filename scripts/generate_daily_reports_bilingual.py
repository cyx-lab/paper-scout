import json
import argparse
import subprocess
import platform
from pathlib import Path
from datetime import datetime

# Project root
ROOT = Path(__file__).resolve().parents[1]


# -----------------------------
# Helpers
# -----------------------------
def render_topics(keyword_hits, lang: str) -> str:
    if not keyword_hits:
        return "（无）\n" if lang == "zh" else "(none)\n"

    # 你的当前格式：list[str]
    if isinstance(keyword_hits, list):
        topics = [str(x).strip() for x in keyword_hits if str(x).strip()]
    # 兼容旧格式：dict[str, int]
    elif isinstance(keyword_hits, dict):
        topics = [str(k).strip() for k in keyword_hits.keys() if str(k).strip()]
    else:
        topics = [str(keyword_hits).strip()] if str(keyword_hits).strip() else []

    # 去重但保序
    seen = set()
    uniq = []
    for t in topics:
        if t not in seen:
            seen.add(t)
            uniq.append(t)

    if not uniq:
        return "（无）\n" if lang == "zh" else "(none)\n"

    return " · ".join(uniq) + "\n"



def _get(d: dict, path: str, default=None):
    """Safe getter for nested dict via 'a.b.c'."""
    cur = d
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _get_lang(d: dict, path: str, lang: str, default=""):
    """
    Get bilingual field: e.g. path='quick_summary' returns d['quick_summary'][lang]
    Also supports nested bilingual object: path='approach.high_level'
    """
    cur = _get(d, path, None)
    if isinstance(cur, dict):
        v = cur.get(lang, default)
        return v if v is not None else default
    return default


def _get_lang_list(d: dict, path: str, lang: str):
    cur = _get(d, path, None)
    if isinstance(cur, dict):
        v = cur.get(lang, [])
        return v if isinstance(v, list) else []
    return []


def _get_list(d: dict, path: str):
    cur = _get(d, path, None)
    return cur if isinstance(cur, list) else []


def _md_escape(s: str) -> str:
    if s is None:
        return ""
    return str(s).replace("\r\n", "\n").strip()


def _md_list(items, empty_line: str):
    items = items or []
    items = [x for x in items if isinstance(x, str) and x.strip()]
    if not items:
        return empty_line + "\n"
    return "".join([f"- {_md_escape(x)}\n" for x in items])


def _yesno(flag: bool, lang: str) -> str:
    if lang == "zh":
        return "是" if flag else "否"
    return "Yes" if flag else "No"


# -----------------------------
# Font helpers
# -----------------------------
def _font_candidates(mainfont: str | None, cjkfont: str | None) -> list[tuple[str, str]]:
    if mainfont and cjkfont:
        return [(mainfont, cjkfont)]

    if platform.system() == "Windows":
        return [(
            mainfont or "Times New Roman",
            cjkfont or "Microsoft YaHei",
        )]

    mainfont_candidates = [mainfont] if mainfont else ["DejaVu Serif", "Liberation Serif"]
    cjkfont_candidates = [cjkfont] if cjkfont else [
        "Noto Serif CJK SC",
        "Noto Sans CJK SC",
        "WenQuanYi Zen Hei",
        "AR PL UMing CN",
    ]
    return [(mf, cf) for mf in mainfont_candidates for cf in cjkfont_candidates]


# -----------------------------
# Load + sort
# -----------------------------
def load_records(meta_dir: Path):
    records = []
    for p in sorted(meta_dir.glob("*.json")):
        if p.name.startswith("_"):
            continue
        with open(p, "r", encoding="utf-8") as f:
            meta = json.load(f)

        paper = meta.get("paper_record", {}) or {}
        signals = paper.get("signals", {}) or {}
        
        keyword_hits = signals.get("keyword_hits", {}) or {}

        score = signals.get("rule_score", None)
        try:
            score_f = float(score)
        except Exception:
            score_f = -1.0

        records.append((score_f, p, meta))

    records.sort(key=lambda x: x[0], reverse=True)
    return records


# -----------------------------
# Render blocks
# -----------------------------
def render_header(run_date: str, lang: str, total: int, done: int) -> str:
    if lang == "zh":
        title = f"每日论文速览（简短摘要 + Takeaway）— {run_date}"
        note = "注：本报告强调快速筛读，突出问题、方法、结论与 takeaway。"
        return (
            f"# {title}\n\n"
            f"- 总论文数：**{total}**\n"
            f"- 已完成 LLM 摘要：**{done}**\n"
            f"- 排序：**rule_score（降序）**\n\n"
            f"> {note}\n\n"
        )
    else:
        title = f"Daily Paper Digest (Short Summary + Takeaway) — {run_date}"
        note = "Note: this digest is optimized for quick triage, highlighting the problem, approach, takeaway, and why it matters."
        return (
            f"# {title}\n\n"
            f"- Total papers: **{total}**\n"
            f"- LLM summarized: **{done}**\n"
            f"- Sorted by: **rule_score (desc)**\n\n"
            f"> {note}\n\n"
        )


def render_paper(meta: dict, score: float, lang: str) -> str:
    paper = meta.get("paper_record", {}) or {}
    assets = meta.get("assets", {}) or {}
    summ = meta.get("llm_summary", {}) or {}
    prov = meta.get("provenance", {}) or {}
    signals = paper.get("signals", {}) or {}
    keyword_hits = signals.get("keyword_hits", None)



    title = paper.get("title", "") or "(No title)"
    arxiv_id = str(paper.get("id", "") or "")
    authors = paper.get("authors", []) or []
    categories = paper.get("categories", []) or []
    pdf_path = assets.get("pdf_path", "") or ""
    pdf_url = assets.get("pdf_url", "") or ""
    summarized_at = prov.get("summarized_at", None)

    L = {
        "value": "\u4ef7\u503c\u7b49\u7ea7\u8bc4\u4f30" if lang == "zh" else "Value assessment",
        "meta": "基本信息" if lang == "zh" else "Metadata",
        "summary": "一句话摘要" if lang == "zh" else "One-sentence summary",
        "prob": "研究问题" if lang == "zh" else "Problem",
        "approach": "采用方法" if lang == "zh" else "Approach",
        "takeaway": "核心 takeaway" if lang == "zh" else "Main takeaway",
        "matters": "为什么值得看" if lang == "zh" else "Why it matters",
        "type": "文章类型" if lang == "zh" else "Paper type",
        "venue": "可能投稿去向" if lang == "zh" else "Likely venue",
        "keywords": "关键词" if lang == "zh" else "Keywords",
    }

    out = []
    out.append("\n---\n\n")
    out.append(f"## {_md_escape(title)}\n\n")
    out.append(f"### {L['meta']}\n\n")
    out.append(f"- **arXiv:** `{arxiv_id}`\n")
    out.append(f"- **rule_score:** `{score}`\n")
    if authors:
        out.append(f"- **authors:** {', '.join([_md_escape(a) for a in authors if str(a).strip()])}\n")
    if categories:
        out.append(f"- **categories:** {', '.join([_md_escape(c) for c in categories if str(c).strip()])}\n")
    if pdf_path:
        out.append(f"- **pdf_path:** `{pdf_path}`\n")
    if pdf_url:
        out.append(f"- **pdf_url:** {pdf_url}\n")
    out.append(f"- **summarized_at:** `{summarized_at}`\n\n")
    
    # related topics
    if lang == "zh":
        out.append("### 相关主题\n\n")
    else:
        out.append("### Related topics\n\n")

    out.append(render_topics(keyword_hits, lang))
    out.append("\n")


    summary_text = _get_lang(summ, "one_sentence_summary", lang, "") or _get_lang(summ, "quick_summary", lang, "")
    out.append(f"### {L['summary']}\n\n{_md_escape(summary_text) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append(f"### {L['prob']}\n\n{_md_escape(_get_lang(summ, 'problem', lang, '')) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    approach_text = _get_lang(summ, "approach", lang, "")
    if not approach_text:
        approach_text = _get_lang(summ, "approach.high_level", lang, "")
    out.append(f"### {L['approach']}\n\n{_md_escape(approach_text) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append(f"### {L['takeaway']}\n\n{_md_escape(_get_lang(summ, 'main_takeaway', lang, '')) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append(f"### {L['matters']}\n\n{_md_escape(_get_lang(summ, 'why_it_matters', lang, '')) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append(f"### {L['value']}\n\n")
    value_level = _get_lang(summ, "value_assessment.level", lang, "")
    value_reason = _get_lang(summ, "value_assessment.reason", lang, "")
    if value_level:
        out.append(f"- **{_md_escape(value_level)}**\n")
        out.append(f"- {_md_escape(value_reason) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    else:
        out.append(f"- {('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append(f"### {L['type']}\n\n{_md_escape(_get_lang(summ, 'paper_type', lang, '')) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append(f"### {L['venue']}\n\n")
    venue_journal = _get(summ, "likely_venue.journal", "") or ""
    venue_conf = _get(summ, "likely_venue.confidence", "") or ""
    venue_reason = _get_lang(summ, "likely_venue.reason", lang, "")
    if venue_journal:
        out.append(f"- **{_md_escape(venue_journal)}**")
        if venue_conf:
            out.append(f" `confidence={_md_escape(venue_conf)}`")
        out.append("\n")
        if venue_reason:
            out.append(f"- {_md_escape(venue_reason)}\n\n")
        else:
            out.append(f"- {('（空）' if lang=='zh' else '(empty)')}\n\n")
    else:
        out.append(f"- {('（空）' if lang=='zh' else '(empty)')}\n\n")
    keywords = _get_list(summ, "keywords")
    out.append(f"### {L['keywords']}\n\n")
    out.append(_md_list(keywords, "- （空）" if lang == "zh" else "- (empty)"))
    out.append("\n")
    return "".join(out)


# -----------------------------
# Markdown -> PDF
# -----------------------------
def md_to_pdf(md_path: Path, *, out_pdf: Path, mainfont: str | None = None, cjkfont: str | None = None):
    """
    Convert markdown to PDF using pandoc + xelatex.
    Try multiple font pairs on Linux runners so PDF generation is less brittle.
    """

    if out_pdf is None:
        pdf_path = md_path.with_suffix(".pdf")
    else:
        pdf_path = Path(out_pdf)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

    err_log = md_path.with_suffix(".pandoc_stderr.txt")
    last_error = None
    with open(err_log, "w", encoding="utf-8") as ef:
        for idx, (mf, cf) in enumerate(_font_candidates(mainfont, cjkfont), start=1):
            cmd = [
                "pandoc",
                str(md_path),
                "-o",
                str(pdf_path),
                "--standalone",
                "--pdf-engine=xelatex",
                "-V", f"mainfont={mf}",
                "-V", f"CJKmainfont={cf}",
                "-V", "geometry:margin=1in",
            ]
            ef.write(f"\n=== Attempt {idx}: mainfont={mf} | cjkfont={cf} ===\n")
            ef.flush()
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=ef)
                print(f"PDF generated with fonts: mainfont={mf}, cjkfont={cf}")
                if err_log.stat().st_size == 0:
                    err_log.unlink()
                return
            except subprocess.CalledProcessError as exc:
                last_error = exc
                ef.write("\n")
                ef.flush()

    if err_log.exists() and err_log.stat().st_size > 0:
        print(f"pandoc stderr saved to: {err_log}")
    if last_error is not None:
        raise last_error


# -----------------------------
# Main
# -----------------------------
def generate_daily_reports():
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?", default=datetime.now().date().isoformat(), help="YYYY-MM-DD (default=today)")
    ap.add_argument("--pdf", action="store_true", help="also generate PDF files")
    ap.add_argument("--mainfont", default=None, help='pandoc -V mainfont=... (optional)')
    ap.add_argument("--cjkfont", default=None, help='pandoc -V CJKmainfont=... (optional)')
    args = ap.parse_args()

    run_date = args.date
    meta_dir = ROOT / "data" / "pdfs" / run_date / "json"
    if not meta_dir.exists():
        raise FileNotFoundError(f"meta_dir not found: {meta_dir}")

    records = load_records(meta_dir)
    if not records:
        print(f"No meta json files found under: {meta_dir}")
        return

    total = len(records)
    done = sum(1 for _, _, meta in records if (meta.get("provenance", {}) or {}).get("summarized_at"))

    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    log_dir = reports_dir / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    out_md_zh = log_dir / f"{run_date}_daily_llm_report_zh.md"
    out_md_en = log_dir / f"{run_date}_daily_llm_report_en.md"

    # Generate ZH
    zh_lines = [render_header(run_date, "zh", total, done)]
    for score, _, meta in records:
        zh_lines.append(render_paper(meta, score, "zh"))
    out_md_zh.write_text("".join(zh_lines), encoding="utf-8")
    print(f"✅ MD written: {out_md_zh}")

    # Generate EN
    en_lines = [render_header(run_date, "en", total, done)]
    for score, _, meta in records:
        en_lines.append(render_paper(meta, score, "en"))
    out_md_en.write_text("".join(en_lines), encoding="utf-8")
    print(f"✅ MD written: {out_md_en}")
    
    pdf_zh_dir = reports_dir / "zh"
    pdf_zh_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_en_dir = reports_dir / "en"
    pdf_en_dir.mkdir(parents=True, exist_ok=True)

    # Convert to PDF
    if args.pdf:
        md_to_pdf(out_md_zh, out_pdf=pdf_zh_dir / f"{run_date}_daily_llm_report_zh.pdf", mainfont=args.mainfont, cjkfont=args.cjkfont)
        md_to_pdf(out_md_en, out_pdf=pdf_en_dir / f"{run_date}_daily_llm_report_en.pdf", mainfont=args.mainfont, cjkfont=args.cjkfont)
        
    print("All done.")


if __name__ == "__main__":
    generate_daily_reports()
