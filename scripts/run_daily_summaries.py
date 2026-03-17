# scripts/run_daily_summaries.py
import os
import sys
import json
import time
import random
import argparse
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv



# -------------------------------------------------
# Ensure project root is on sys.path
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.llm.schema_checker import validate_json_against_schema

load_dotenv()
# -------------------------------------------------
# Config
# -------------------------------------------------
MY_API_KEY = os.getenv("MY_API_KEY")
API_KEY = MY_API_KEY
if not API_KEY:
    raise RuntimeError("Missing API key: set OPENROUTER_API_KEY or MY_API_KEY in .env")

# Default base url follows selected key type:
# - OPENROUTER_API_KEY -> openrouter
# - MY_API_KEY         -> uiuiapi (legacy setup in this project)
BASE_URL = os.getenv("MY_API_BASE_URL", "https://api1.uiuiapi.com/v1")

MODEL = os.getenv("LLM_MODEL", "gemini-3-flash-preview")
DEFAULT_WORKERS = int(os.getenv("LLM_WORKERS", "2"))
MAX_API_RETRIES = int(os.getenv("LLM_MAX_API_RETRIES", "5"))
RETRY_BASE_SLEEP = float(os.getenv("LLM_RETRY_BASE_SLEEP", "1.5"))
RETRY_MAX_SLEEP = float(os.getenv("LLM_RETRY_MAX_SLEEP", "20"))
LLM_USE_JSON_SCHEMA = os.getenv("LLM_USE_JSON_SCHEMA", "0").strip().lower() in {
    "1", "true", "yes", "on"
}
SCHEMA_MODE_ENABLED = LLM_USE_JSON_SCHEMA

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

TRANSIENT_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


def _extract_status_code(err: Exception):
    if hasattr(err, "status_code"):
        try:
            code = int(getattr(err, "status_code"))
            if 100 <= code <= 599:
                return code
        except Exception:
            pass

    msg = str(err)
    m = re.search(r"Error code:\s*(\d{3})", msg)
    if m:
        return int(m.group(1))
    return None


def _is_transient_api_error(err: Exception) -> bool:
    code = _extract_status_code(err)
    if code in TRANSIENT_STATUS_CODES:
        return True

    msg = str(err).lower()
    transient_hints = [
        "service temporarily unavailable",
        "temporarily unavailable",
        "timeout",
        "timed out",
        "connection reset",
        "overloaded",
        "rate limit",
    ]
    return any(h in msg for h in transient_hints)


def _chat_create_with_retry(**kwargs):
    last_err = None
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            last_err = e
            if (not _is_transient_api_error(e)) or attempt >= MAX_API_RETRIES:
                raise

            sleep_s = min(RETRY_MAX_SLEEP, RETRY_BASE_SLEEP * (2 ** (attempt - 1)))
            sleep_s += random.uniform(0.0, 0.4)
            code = _extract_status_code(e)
            print(
                f"[RETRY] transient API error code={code} "
                f"(attempt {attempt}/{MAX_API_RETRIES}), sleep={sleep_s:.1f}s"
            )
            time.sleep(sleep_s)

    raise last_err


def _should_fallback_from_schema_error(err: Exception) -> bool:
    msg = str(err).lower()
    hints = [
        "response_format",
        "response_schema",
        "generation_config.response_schema",
        "additionalproperties",
        "unknown name",
        "invalid json payload",
        "json_schema",
    ]
    return any(h in msg for h in hints)

SYSTEM_PROMPT = r"""你是一名凝聚态物理论文的速读助手。

我会给你一篇论文的全文文本。你的任务不是写长篇分析，而是为日报生成“简短摘要 + takeaway”。

请严格遵守以下要求：
- 只基于论文中明确出现的内容，不要编造。
- 输出风格要简洁、信息密度高，适合日报快速浏览。
- 不要写公式，不要写 LaTeX，不要写复杂技术细节。
- 不要评价论文质量高低，只说明它研究了什么、做了什么、得出了什么。
- 中英文内容语义一致，但不要求逐字翻译。
- 关键词控制在 3 到 6 个。
- 输出必须严格符合给定 JSON Schema。
- 只输出 JSON，不要任何解释文字，不要 markdown 代码块。
"""

# 日报精简 schema
LLM_SUMMARY_SCHEMA = {
    "name": "condmat_paper_digest_minimal",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "one_sentence_summary": {
                "type": "object",
                "properties": {
                    "zh": {"type": "string"},
                    "en": {"type": "string"}
                },
                "required": ["zh", "en"]
            },
            "problem": {
                "type": "object",
                "properties": {
                    "zh": {"type": "string"},
                    "en": {"type": "string"}
                },
                "required": ["zh", "en"]
            },
            "approach": {
                "type": "object",
                "properties": {
                    "zh": {"type": "string"},
                    "en": {"type": "string"}
                },
                "required": ["zh", "en"]
            },
            "main_takeaway": {
                "type": "object",
                "properties": {
                    "zh": {"type": "string"},
                    "en": {"type": "string"}
                },
                "required": ["zh", "en"]
            },
            "why_it_matters": {
                "type": "object",
                "properties": {
                    "zh": {"type": "string"},
                    "en": {"type": "string"}
                },
                "required": ["zh", "en"]
            },
            "paper_type": {
                "type": "object",
                "properties": {
                    "zh": {"type": "string"},
                    "en": {"type": "string"}
                },
                "required": ["zh", "en"]
            },
            "likely_venue": {
                "type": "object",
                "properties": {
                    "journal": {"type": "string"},
                    "confidence": {
                        "type": "string",
                        "enum": ["low", "medium", "high"]
                    },
                    "reason": {
                        "type": "object",
                        "properties": {
                            "zh": {"type": "string"},
                            "en": {"type": "string"}
                        },
                        "required": ["zh", "en"]
                    }
                },
                "required": ["journal", "confidence", "reason"]
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": [
            "one_sentence_summary",
            "problem",
            "approach",
            "main_takeaway",
            "why_it_matters",
            "paper_type",
            "likely_venue",
            "keywords"
        ]
    }
}

# -------------------------------------------------
# Utilities
# -------------------------------------------------
def pdf_to_text(pdf_path: Path) -> str:
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = (page.extract_text() or "").strip()
            if text:
                chunks.append(text)
    return "\n\n".join(chunks)


def _extract_first_json_object(text: str) -> str:
    """
    兼容模型偶尔输出 ```json ... ``` 或夹杂少量文字的情况。
    """
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model output")

    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]

    raise ValueError("Unclosed JSON object in model output")


def _repair_invalid_json_escapes(text: str) -> str:
    r"""
    Repair common malformed JSON escapes from LLM output by doubling isolated
    backslashes that are invalid inside JSON strings.
    """
    return re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r"\\\\", text)


def _load_llm_json(raw_text: str) -> dict:
    """
    Parse model JSON with a lightweight escape repair fallback.
    """
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        if "Invalid \\escape" not in str(e):
            raise

    repaired = _repair_invalid_json_escapes(raw_text)
    return json.loads(repaired)


def build_parse_fix_prompt(raw_output: str, parse_error: str) -> str:
    return f"""
下面这段内容本应是一个 JSON 对象，但解析失败了。

【解析错误】：
{parse_error}

【原始输出】：
{raw_output}

请把它重写为一个合法的 JSON 对象。
要求：
- 只输出一个完整 JSON 对象
- 不要输出 markdown 代码块
- 如果字符串里包含反斜杠，必须写成双反斜杠
- 不要新增解释文字
""".strip()


def call_llm_json(paper_text: str, *, use_schema: bool = True) -> dict:
    """
    先尝试 response_format=json_schema（有时中转不支持会 400）。
    如果遇到 response_format 相关 400，则自动降级为纯 JSON 模式（prompt 强约束 + 本地 json.loads）。
    """
    user_msg = "下面是论文全文文本，请基于全文输出 JSON：\n\n" + paper_text

    # --- first try: json_schema mode
    global SCHEMA_MODE_ENABLED
    if use_schema and SCHEMA_MODE_ENABLED:
        try:
            resp = _chat_create_with_retry(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_schema", "json_schema": LLM_SUMMARY_SCHEMA},
                temperature=0.2,
            )
            return _load_llm_json(resp.choices[0].message.content)
        except Exception as e:
            if not _should_fallback_from_schema_error(e):
                raise
            SCHEMA_MODE_ENABLED = False
            print(f"[SCHEMA_FALLBACK] {e}")

    # --- fallback: pure JSON
    resp = _chat_create_with_retry(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "请严格只输出一个 JSON 对象，不要任何解释文字，不要 markdown 代码块。"
                    "如果 JSON 字符串中出现反斜杠，请使用双反斜杠转义。\n\n"
                    + user_msg
                ),
            },
        ],
        temperature=0.2,
    )
    raw = resp.choices[0].message.content
    raw_json = _extract_first_json_object(raw)
    try:
        return _load_llm_json(raw_json)
    except json.JSONDecodeError as e:
        fix_prompt = build_parse_fix_prompt(raw_json, str(e))
        resp2 = _chat_create_with_retry(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": fix_prompt},
            ],
            temperature=0.1,
        )
        return _load_llm_json(_extract_first_json_object(resp2.choices[0].message.content))


def build_fix_prompt(original_output: dict, errors: list[str], allowed_fields: list[str]) -> str:
    err_block = "\n".join(f"- {e}" for e in errors)
    return f"""
你的上一版 JSON 输出未通过 schema 校验。

【合法顶层字段名仅限以下这些（不得新增、不得改名）】：
{allowed_fields}

【校验错误（路径: 原因）】：
{err_block}

【你上一版的完整输出】：
{json.dumps(original_output, ensure_ascii=False, indent=2)}

请你根据错误原因修正 JSON，使其严格符合 schema。
要求：
- 输出必须是一个完整 JSON
- 不要新增任何字段；不要改字段名；不要输出解释文字
只输出 JSON。
""".strip()


def extract_with_one_fix_retry(paper_text: str) -> dict:
    """
    你想要的逻辑：
    - 第一次生成并校验
    - 不通过：把错误原因发给 LLM 再生成一次
    - 仍不通过：失败
    """
    global SCHEMA_MODE_ENABLED
    allowed_fields = list(LLM_SUMMARY_SCHEMA["schema"]["properties"].keys())

    out1 = call_llm_json(paper_text, use_schema=True)
    errors1 = validate_json_against_schema(out1, LLM_SUMMARY_SCHEMA)
    if not errors1:
        return out1

    fix_prompt = build_fix_prompt(out1, errors1, allowed_fields)

    # 第二次：依旧先尝试 schema，如果不支持会降级
    out2 = None
    if SCHEMA_MODE_ENABLED:
        try:
            resp = _chat_create_with_retry(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": fix_prompt},
                ],
                response_format={"type": "json_schema", "json_schema": LLM_SUMMARY_SCHEMA},
                temperature=0.1,
            )
            out2 = json.loads(resp.choices[0].message.content)
        except Exception as e:
            if _should_fallback_from_schema_error(e):
                SCHEMA_MODE_ENABLED = False
                print(f"[SCHEMA_FALLBACK] {e}")
            else:
                raise

    if out2 is None:
        # fallback: pure JSON
        resp = _chat_create_with_retry(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Output one JSON object only, no markdown, no explanations. "
                        "If backslashes appear inside JSON strings, escape them as double backslashes.\n\n"
                        + fix_prompt
                    ),
                },
            ],
            temperature=0.1,
        )
        raw_out2 = _extract_first_json_object(resp.choices[0].message.content)
        try:
            out2 = _load_llm_json(raw_out2)
        except json.JSONDecodeError as e:
            repair_prompt = build_parse_fix_prompt(raw_out2, str(e))
            resp_fix = _chat_create_with_retry(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": repair_prompt},
                ],
                temperature=0.1,
            )
            out2 = _load_llm_json(_extract_first_json_object(resp_fix.choices[0].message.content))

    errors2 = validate_json_against_schema(out2, LLM_SUMMARY_SCHEMA)
    if not errors2:
        return out2

    raise RuntimeError(
        "Schema validation failed after one fix retry.\n"
        "First pass errors:\n- " + "\n- ".join(errors1) + "\n\n"
        "Second pass errors:\n- " + "\n- ".join(errors2)
    )


def should_skip(meta: dict) -> bool:
    """
    跳过已完成的：summarized_at 存在且非空
    """
    prov = meta.get("provenance", {})
    return bool(prov.get("summarized_at"))


def process_one_meta(meta_json_path: Path) -> dict:
    """
    返回：结果 dict（用于汇总打印 / 写日志）
    """
    t0 = time.time()
    try:
        with open(meta_json_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        if should_skip(meta):
            return {"file": meta_json_path.name, "status": "skipped", "secs": 0.0}

        pdf_rel = meta["assets"]["pdf_path"]
        pdf_path = ROOT / pdf_rel
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        text = pdf_to_text(pdf_path)
        if not text:
            raise RuntimeError("PDF text extraction returned empty content")

        # 小随机抖动，降低并发时撞到同一后端的概率
        time.sleep(random.uniform(0.05, 0.25))

        summary = extract_with_one_fix_retry(text)

        meta["llm_summary"].update(summary)
        meta.setdefault("provenance", {})
        meta["provenance"]["llm_model"] = MODEL
        meta["provenance"]["summarized_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        meta["provenance"]["input_scope"] = "full_pdf_text"

        with open(meta_json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return {"file": meta_json_path.name, "status": "ok", "secs": round(time.time() - t0, 2)}

    except Exception as e:
        return {"file": meta_json_path.name, "status": "fail", "error": str(e), "secs": round(time.time() - t0, 2)}

'''
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date", nargs="?", default=datetime.now().date().isoformat(), help="YYYY-MM-DD, default=today")
    parser.add_argument("--workers", type=int, default=4, help="number of concurrent workers")
    args = parser.parse_args()

    run_date = args.date
    workers = args.workers

    meta_dir = ROOT / "data" / "pdfs" / run_date / "json"
    if not meta_dir.exists():
        raise FileNotFoundError(f"Meta dir not found: {meta_dir}")

    meta_files = sorted(meta_dir.glob("*.json"))
    if not meta_files:
        print(f"No meta json files found under: {meta_dir}")
        return

    print(f"Run date: {run_date}")
    print(f"Meta files: {len(meta_files)}")
    print(f"Workers: {workers}")
    print("-" * 80)

    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process_one_meta, p): p for p in meta_files}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            if r["status"] == "ok":
                print(f"[OK]      {r['file']} ({r['secs']}s)")
            elif r["status"] == "skipped":
                print(f"[SKIPPED] {r['file']}")
            else:
                print(f"[FAIL]    {r['file']} ({r['secs']}s)")
                print("          ", r.get("error", "")[:300])

    ok = sum(1 for r in results if r["status"] == "ok")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    fail = sum(1 for r in results if r["status"] == "fail")

    print("-" * 80)
    print(f"Done. ok={ok}, skipped={skipped}, fail={fail}")

    # 写一份运行日志，方便你回看失败原因
    log_path = meta_dir / "_summarize_run_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(
            {"run_date": run_date, "workers": workers, "results": results},
            f,
            ensure_ascii=False,
            indent=2
        )
    print(f"Log written: {log_path}")
'''

def run_summaries():
    parser = argparse.ArgumentParser()
    parser.add_argument("date", nargs="?", default=datetime.now().date().isoformat(), help="YYYY-MM-DD, default=today")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="number of concurrent workers")

    # 新增：失败循环重跑控制
    parser.add_argument("--max-rounds", type=int, default=4, help="max retry rounds for failed metas")
    parser.add_argument("--max-attempts-per-file", type=int, default=4, help="max total attempts per meta file")

    args = parser.parse_args()

    run_date = args.date
    workers = args.workers

    meta_dir = ROOT / "data" / "pdfs" / run_date / "json"
    if not meta_dir.exists():
        raise FileNotFoundError(f"Meta dir not found: {meta_dir}")

    meta_files_all = sorted(
        p for p in meta_dir.glob("*.json")
        if not p.name.startswith("_")
    )

    if not meta_files_all:
        print(f"No meta json files found under: {meta_dir}")
        return

    print(f"Run date: {run_date}")
    print(f"Meta files: {len(meta_files_all)}")
    print(f"Workers: {workers}")
    print("-" * 80)

    # attempt 计数：防止某些永久失败导致死循环
    attempts: dict[str, int] = {p.name: 0 for p in meta_files_all}

    # 第一轮：跑全部；后续轮次：只跑失败
    pending = meta_files_all[:]
    all_results = []  # 保存每次执行的结果（包含轮次信息）

    round_idx = 1
    while pending and round_idx <= args.max_rounds:
        print(f"\n[ROUND {round_idx}] pending={len(pending)}")
        round_results = []

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {}
            for p in pending:
                if attempts[p.name] >= args.max_attempts_per_file:
                    # 已达到最大尝试次数，直接标记为 fail，不再提交
                    r = {
                        "file": p.name,
                        "status": "fail",
                        "error": f"Reached max attempts ({args.max_attempts_per_file})",
                        "secs": 0.0,
                        "round": round_idx,
                        "attempt": attempts[p.name],
                    }
                    round_results.append(r)
                    all_results.append(r)
                    continue

                attempts[p.name] += 1
                futs[ex.submit(process_one_meta, p)] = p

            for fut in as_completed(futs):
                p = futs[fut]
                r = fut.result()
                r["round"] = round_idx
                r["attempt"] = attempts[p.name]
                round_results.append(r)
                all_results.append(r)

                if r["status"] == "ok":
                    print(f"[OK]      {r['file']} ({r['secs']}s)  attempt={r['attempt']}")
                elif r["status"] == "skipped":
                    print(f"[SKIPPED] {r['file']}")
                else:
                    print(f"[FAIL]    {r['file']} ({r['secs']}s)  attempt={r['attempt']}")
                    print("          ", r.get("error", "")[:300])

        # 计算下一轮要重跑的文件：只重跑 fail，且没超过 max_attempts_per_file
        failed_names = {r["file"] for r in round_results if r["status"] == "fail"}
        pending = [
            (meta_dir / name)
            for name in sorted(failed_names)
            if attempts.get(name, 0) < args.max_attempts_per_file
        ]

        ok = sum(1 for r in round_results if r["status"] == "ok")
        skipped = sum(1 for r in round_results if r["status"] == "skipped")
        fail = sum(1 for r in round_results if r["status"] == "fail")

        print(f"[ROUND {round_idx} SUMMARY] ok={ok}, skipped={skipped}, fail={fail}")

        if fail == 0:
            break

        round_idx += 1

    # 最终统计
    final_ok = sum(1 for r in all_results if r["status"] == "ok")
    final_skipped = sum(1 for r in all_results if r["status"] == "skipped")

    # 注意：一个文件可能多次 fail 后成功，所以最终 fail 需要按“最后一次状态”统计更合理
    # 这里给出“仍未成功且达到上限 / 轮次用尽”的文件数量
    last_status = {}
    for r in all_results:
        last_status[r["file"]] = r["status"]

    still_fail = sum(1 for f, st in last_status.items() if st == "fail")

    print("-" * 80)
    print(f"Done. ok={final_ok}, skipped={final_skipped}, still_fail={still_fail}, rounds={round_idx if all_results else 0}")

    # 写运行日志（包含每轮 / 每次 attempt）
    log_path = meta_dir / "_summarize_run_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_date": run_date,
                "workers": workers,
                "max_rounds": args.max_rounds,
                "max_attempts_per_file": args.max_attempts_per_file,
                "attempts": attempts,
                "results": all_results,
            },
            f,
            ensure_ascii=False,
            indent=2
        )
    print(f"Log written: {log_path}")

    if still_fail > 0:
        print("Still failed files (last status=fail):")
        for name, st in sorted(last_status.items()):
            if st == "fail":
                print(" -", name)

if __name__ == "__main__":
    run_summaries()

