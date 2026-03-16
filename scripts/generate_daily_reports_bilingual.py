import json
import argparse
import subprocess
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
        title = f"每日论文速览（LLM 摘要）— {run_date}"
        note = "注：图/表/公式细节未必可靠；本报告用于快速筛选与导航精读。"
        return (
            f"# {title}\n\n"
            f"- 总论文数：**{total}**\n"
            f"- 已完成 LLM 摘要：**{done}**\n"
            f"- 排序：**rule_score（降序）**\n\n"
            f"> {note}\n\n"
        )
    else:
        title = f"Daily Paper Digest (LLM Summaries) — {run_date}"
        note = "Note: figure/table/formula details may be unreliable; this digest is for rapid triage and navigation."
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

    # Labels per language
    L = {
        "meta": "基本信息" if lang == "zh" else "Metadata",
        "quick": "快速总结" if lang == "zh" else "Quick summary",
        "bg": "研究背景" if lang == "zh" else "Background",
        "prob": "研究问题" if lang == "zh" else "Problem",
        "approach": "方法与思路" if lang == "zh" else "Approach",
        "tech": "技术细节" if lang == "zh" else "Technical details",
        "exp": "实验/应用关联" if lang == "zh" else "Experiments / Applications",
        "innov": "创新点" if lang == "zh" else "Innovations",
        "prior": "与已有工作关系" if lang == "zh" else "Prior work & relation",
        "assump": "假设与适用范围" if lang == "zh" else "Assumptions & validity",
        "ka": "关键假设" if lang == "zh" else "Key assumptions",
        "vr": "适用范围" if lang == "zh" else "Valid regimes",
        "fm": "失效/局限" if lang == "zh" else "Failure modes / limits",
        "insight": "物理洞见" if lang == "zh" else "Physical insight",
        "intu": "直觉/物理图像" if lang == "zh" else "Intuition",
        "chg": "理解上的变化" if lang == "zh" else "What changes in understanding",
        "open": "开放问题与后续" if lang == "zh" else "Open questions & future",
        "journal": "可能投稿期刊" if lang == "zh" else "Journal positioning",
        "mentioned": "是否提到" if lang == "zh" else "Mentioned",
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


    # quick/background/problem
    out.append(f"### {L['quick']}\n\n{_md_escape(_get_lang(summ, 'quick_summary', lang, '')) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append(f"### {L['bg']}\n\n{_md_escape(_get_lang(summ, 'background', lang, '')) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append(f"### {L['prob']}\n\n{_md_escape(_get_lang(summ, 'problem', lang, '')) or ('（空）' if lang=='zh' else '(empty)')}\n\n")

    # approach
    out.append(f"### {L['approach']}\n\n")
    out.append(f"**{('高层概述' if lang=='zh' else 'High-level')}:** ")
    out.append(f"{_md_escape(_get_lang(summ, 'approach.high_level', lang, '')) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append("\n")

    # experiment/application
    mentioned = bool(_get(summ, "experiment_or_application.mentioned", False))
    items = _get(summ, "experiment_or_application.items", []) or []
    out.append(f"### {L['exp']}\n\n")
    out.append(f"- **{L['mentioned']}:** {_yesno(mentioned, lang)}\n")
    if not mentioned or not items:
        out.append(f"- {('（无）' if lang=='zh' else '(none)')}\n\n")
    else:
        for i, it in enumerate(items, 1):
            sc = _get_lang(it, "scenario", lang, "")
            ob = _get_lang(it, "observable_or_signal", lang, "")
            pf = _get_lang(it, "platform", lang, "")
            out.append(f"\n**Item {i}**\n\n")
            out.append(f"- {('场景' if lang=='zh' else 'Scenario')}: {_md_escape(sc)}\n")
            out.append(f"- {('可观测量/信号' if lang=='zh' else 'Observable/signal')}: {_md_escape(ob)}\n")
            out.append(f"- {('平台' if lang=='zh' else 'Platform')}: {_md_escape(pf)}\n")
        out.append("\n")

    # innovations / prior work
    out.append(f"### {L['innov']}\n\n")
    out.append(_md_list(_get_lang_list(summ, "innovations", lang), "- （空）" if lang=="zh" else "- (empty)"))
    out.append("\n")

    out.append(f"### {L['prior']}\n\n")
    out.append(_md_list(_get_lang_list(summ, "prior_work_and_relation", lang), "- （空）" if lang=="zh" else "- (empty)"))
    out.append("\n")

    # assumptions
    out.append(f"### {L['assump']}\n\n")
    out.append(f"**{L['ka']}:**\n")
    out.append(_md_list(_get_lang_list(summ, "assumptions_and_validity.key_assumptions", lang), "- （空）" if lang=="zh" else "- (empty)"))
    out.append("\n")
    out.append(f"**{L['vr']}:**\n")
    out.append(_md_list(_get_lang_list(summ, "assumptions_and_validity.valid_regimes", lang), "- （空）" if lang=="zh" else "- (empty)"))
    out.append("\n")
    out.append(f"**{L['fm']}:**\n")
    out.append(_md_list(_get_lang_list(summ, "assumptions_and_validity.failure_modes_or_limits", lang), "- （空）" if lang=="zh" else "- (empty)"))
    out.append("\n")

    # physical insight
    out.append(f"### {L['insight']}\n\n")
    out.append(f"**{L['intu']}:** ")
    out.append(f"{_md_escape(_get_lang(summ, 'physical_insight.intuition', lang, '')) or ('（空）' if lang=='zh' else '(empty)')}\n\n")
    out.append(f"**{L['chg']}:**\n")
    out.append(_md_list(_get_lang_list(summ, "physical_insight.what_changes_in_understanding", lang), "- （空）" if lang=="zh" else "- (empty)"))
    out.append("\n")

    # open questions
    out.append(f"### {L['open']}\n\n")
    out.append(_md_list(_get_lang_list(summ, "open_questions_and_future", lang), "- （空）" if lang=="zh" else "- (empty)"))
    out.append("\n")

    # journal positioning
    out.append(f"### {L['journal']}\n\n")
    journals = _get(summ, "journal_positioning.suggested_journals", []) or []
    if not journals:
        out.append("- （空）\n" if lang == "zh" else "- (empty)\n")
    else:
        for i, j in enumerate(journals, 1):
            journal = _get(j, "journal", "") or ""
            conf = _get(j, "confidence", "") or ""
            reason = _get_lang(j, "reason", lang, "")
            out.append(f"- **{_md_escape(journal) or 'Unknown'}**  `confidence={conf or 'unknown'}`\n")
            if reason.strip():
                out.append(f"  - {_md_escape(reason)}\n")
            else:
                out.append(f"  - {('（空）' if lang=='zh' else '(empty)')}\n")

    out.append("\n")
    return "".join(out)


# -----------------------------
# Markdown -> PDF
# -----------------------------
def md_to_pdf(md_path: Path, *, out_pdf: Path, mainfont: str | None = None, cjkfont: str | None = None):
    """
    Convert markdown to PDF using pandoc + xelatex, with robust CJK font handling on Windows.
    """
    
    if out_pdf is None:
        pdf_path = md_path.with_suffix(".pdf")
    else:
        pdf_path = Path(out_pdf)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # “默认兜底字体”
    if mainfont is None:
        mainfont = "Times New Roman"
    if cjkfont is None:
        cjkfont = "Microsoft YaHei"   # 或者 "SimSun"

    cmd = [
        "pandoc",
        str(md_path),
        "-o",
        str(pdf_path),
        "--standalone",
        "--pdf-engine=xelatex",
        "-V", f"mainfont={mainfont}",
        "-V", f"CJKmainfont={cjkfont}",
        "-V", "geometry:margin=1in",
    ]
    
    
    err_log = md_path.with_suffix(".pandoc_stderr.txt")
    with open(err_log, "w", encoding="utf-8") as ef:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=ef)

    if err_log.stat().st_size == 0:
        err_log.unlink()  # 删除空文件
    else:
        print(f"⚠️ pandoc stderr saved to: {err_log}")
    
    


# -----------------------------
# Main
# -----------------------------
def generate_daily_reports():
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?", default=datetime.now().date().isoformat(), help="YYYY-MM-DD (default=today)")
    ap.add_argument("--no-pdf", action="store_true", help="only generate md, skip pdf conversion")
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
    if not args.no_pdf:
        md_to_pdf(out_md_zh, out_pdf=pdf_zh_dir / f"{run_date}_daily_llm_report_zh.pdf", mainfont=args.mainfont, cjkfont=args.cjkfont)
        md_to_pdf(out_md_en, out_pdf=pdf_en_dir / f"{run_date}_daily_llm_report_en.pdf", mainfont=args.mainfont, cjkfont=args.cjkfont)
        
    print("All done.")


if __name__ == "__main__":
    generate_daily_reports()
