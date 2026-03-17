import sys
import os
import json
import yaml
from datetime import datetime
from pathlib import Path

# -------------------------------------------------
# Ensure project root is on sys.path (for direct run)
# -------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT)

from src.connectors.arxiv_api import fetch_arxiv
from src.retrieval.rules import apply_rule_filter
from src.reporting.markdown import write_daily_markdown_report, ReportMeta
from src.download.pdf_downloader import download_papers


def build_download_map(downloaded_paths: list[Path]) -> dict[str, Path]:
    """
    downloader 文件名规则：<score>_<title>__<arxiv_id>.pdf
    这里从文件名中抽取 <arxiv_id>，映射到 PDF Path。
    """
    m: dict[str, Path] = {}
    for p in downloaded_paths:
        name = p.name
        if "__" not in name:
            continue
        tail = name.split("__", 1)[1]
        if not tail.lower().endswith(".pdf"):
            continue
        arxiv_id = tail[:-4]  # remove ".pdf"
        m[arxiv_id] = p
    return m


def empty_bilingual_summary() -> dict:
    """
    生成一个空的中英双语 llm_summary 结构，后续由 LLM 填充。
    目标是日报速读：简短摘要 + takeaway。
    """
    return {
        "one_sentence_summary": {"zh": "", "en": ""},
        "problem": {"zh": "", "en": ""},
        "approach": {"zh": "", "en": ""},
        "main_takeaway": {"zh": "", "en": ""},
        "why_it_matters": {"zh": "", "en": ""},
        "paper_type": {"zh": "", "en": ""},
        "likely_venue": {
            "journal": "",
            "confidence": "low",
            "reason": {"zh": "", "en": ""},
        },
        "keywords": [],
    }



def write_meta_jsons(
    records: list,
    *,
    project_root: Path,
    run_date: str,
    mode_name: str,
    profile_name: str,
    meta_dir: Path,
    overwrite: bool = False,
) -> int:
    """
    JSON 单独写到 meta_dir 下：json/<arxiv_id>.json
    JSON 中的 assets.pdf_path 永远写相对 project_root 的路径，便于迁移与后续 LLM pipeline 使用。
    同时一次性生成空的 llm_summary（中英双语结构），后续 summarizer 只需要“填值”。
    """
    meta_dir.mkdir(parents=True, exist_ok=True)
    n = 0

    for r in records:
        if not (getattr(r, "assets", None) and getattr(r.assets, "pdf_path", None)):
            continue

        arxiv_id = str(r.id).replace("/", "_")
        json_path = meta_dir / f"{arxiv_id}.json"
        if json_path.exists() and not overwrite:
            continue

        pdf_rel = r.assets.pdf_path  # ✅ 相对 ROOT 的路径

        payload = {
            # 事实层：论文信息与规则筛选结果（可回溯）
            "paper_record": r.model_dump(mode="json"),

            # 常用快捷字段（避免 downstream 深挖结构）
            "assets": {
                "pdf_path": pdf_rel,  # ✅ 相对路径（相对 project_root）
                "pdf_url": getattr(r.assets, "pdf_url", None),
                "pdf_filename": Path(pdf_rel).name,
            },

            # ✅ 一次性生成“空的”中英双语结构，后续由 LLM 填充
            "llm_summary": empty_bilingual_summary(),

            "provenance": {
                "run_date": run_date,
                "profile_name": profile_name,
                "mode_name": mode_name,
                # 下面这些字段后续 summarizer 写回即可
                "llm_prompt_version": "v2-daily-digest-takeaway",
                "llm_model": None,
                "summarized_at": None,
                "input_scope": None,  # e.g. "abstract+first_2_pages"
            },
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        n += 1

    return n



    # -------------------------------------------------
    # Load profile config
    # -------------------------------------------------
def fetch_and_process():
    profile_path = os.path.join(ROOT, "config", "profiles", "my_phd_config.yaml")
    with open(profile_path, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    mode_name = "daily"
    mode = profile["modes"][mode_name]
    fetch_cfg = mode["fetch"]
    rules_cfg = mode["rules"]

    # -------------------------------------------------
    # Fetch arXiv papers
    # -------------------------------------------------
    recs = fetch_arxiv(
        categories=fetch_cfg["categories"],
        time_window=fetch_cfg["time_window"],
        max_results=fetch_cfg.get("max_fetch", 200),
    )
    print(f"Fetched: {len(recs)} papers")

    # -------------------------------------------------
    # Apply rule-based filtering
    # -------------------------------------------------
    kept, dropped = apply_rule_filter(recs, rules_cfg)
    print(f"Kept: {len(kept)} | Dropped: {len(dropped)}")

    # -------------------------------------------------
    # Write Markdown report (existing rule-based report)
    # -------------------------------------------------
    today = datetime.now().date().isoformat()
    profile_name = os.path.splitext(os.path.basename(profile_path))[0]

    reports_dir = Path(ROOT) / "reports"
    log_dir = reports_dir / "log"
    log_dir.mkdir(parents=True, exist_ok=True)

    out_path = log_dir / f"{today}_{mode_name}_raw.md"

    meta = ReportMeta(
        date=today,
        profile_name=profile_name,
        mode_name=mode_name,
        fetched=len(recs),
        kept=len(kept),
        dropped=len(dropped),
    )

    write_daily_markdown_report(
        out_path=out_path,
        records_ranked=kept,
        meta=meta,
        include_rule_signals=True,
    )
    print(f"\n✅ Wrote markdown report: {out_path}")

    # -------------------------------------------------
    # Inspect top results
    # -------------------------------------------------
    print("\n===== TOP KEPT (by rule_score) =====")
    for r in kept[:10]:
        print("-" * 80)
        print(f"{r.id}")
        print(f"score={r.signals.rule_score} | author_match={r.signals.author_match}")
        print(r.title)
        print("hits:", r.signals.keyword_hits)
        print("categories:", r.categories)
        print("pdf:", r.assets.pdf_url)

    # -------------------------------------------------
    # Download PDFs
    # -------------------------------------------------
    to_download = kept

    pdf_dir = Path(ROOT) / "data" / "pdfs" / today
    pdf_dir.mkdir(parents=True, exist_ok=True)

    downloaded = download_papers(
        to_download,
        pdf_dir,
        sleep_s=1.0,      # polite delay
        overwrite=False,  # 已存在就跳过
    )
    print(f"\nDownloaded {len(downloaded)} PDFs to: {pdf_dir}")

    # -------------------------------------------------
    # Fill assets.pdf_path as RELATIVE path (relative to ROOT)
    # -------------------------------------------------
    dl_map = build_download_map(downloaded)

    filled = 0
    for r in to_download:
        arxiv_id_key = str(r.id).replace("/", "_")
        p = dl_map.get(arxiv_id_key)
        if p is None:
            continue

        # ✅ 关键：保持相对路径（从 paper-scout 根目录出发）
        r.assets.pdf_path = os.path.relpath(str(p), ROOT)
        filled += 1

    print(f"Filled assets.pdf_path for {filled} records (relative to project root)")

    # -------------------------------------------------
    # Write JSON meta files to a separate folder
    # -------------------------------------------------
    meta_dir = pdf_dir / "json"
    n_json = write_meta_jsons(
        to_download,
        project_root=Path(ROOT),
        run_date=today,
        mode_name=mode_name,
        profile_name=profile_name,
        meta_dir=meta_dir,
        overwrite=False,
    )

    print(f"\n✅ Wrote {n_json} JSON meta files to: {meta_dir}")
    print("\nDirectory layout example:")
    print(f"  {pdf_dir}/")
    print("    <score>_<title>__<arxiv_id>.pdf")
    print(f"    json/{'<arxiv_id>'}.json")
    return

if __name__ == "__main__":
    fetch_and_process()
