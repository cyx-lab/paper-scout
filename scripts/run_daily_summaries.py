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

SYSTEM_PROMPT = r"""浣犳槸涓€鍚嶅嚌鑱氭€佺墿鐞嗙爺绌惰€呯殑璁烘枃蹇€熼槄璇诲姪鎵嬨€?

鎴戜細缁欎綘涓€绡囩煭绡囧嚌鑱氭€佺墿鐞嗚鏂囷紙PRL 椋庢牸锛?=10 椤碉級鐨勫叏鏂囨枃鏈€?
浣犵殑浠诲姟鏄府鍔╃爺绌惰€呪€滃揩閫熺悊瑙ｈ繖绡囪鏂囧湪鐗╃悊涓婂仛浜嗕粈涔堚€濄€?

璇蜂弗鏍奸伒瀹堜互涓嬪師鍒欙細
- 杈撳嚭涓€涓猼ypora鍙鐨刴arkdown鏂囨湰銆?
- 鍙熀浜庤鏂囨枃鏈腑鏄庣‘鍑虹幇鐨勫唴瀹癸紝涓嶈缂栭€犮€?
- 涓嶅璁烘枃璐ㄩ噺銆侀噸瑕佹€с€佸閿欏仛璇勪环銆?
- 濡傛灉鏌愪簺淇℃伅涓嶆竻妤氾紝鍙互缁欏嚭淇濆畧銆佹鎷€х殑鎻忚堪銆?
- 涓嫳鏂囧唴瀹瑰簲璇箟涓€鑷达紝浣嗕笉鏄€愬瓧缈昏瘧銆?
- 杈撳嚭蹇呴』涓ユ牸绗﹀悎鎴戞彁渚涚殑 JSON Schema銆?
- 鍙緭鍑?JSON锛屼笉瑕佷换浣曡В閲婃€ф枃瀛椼€?
- 濡傛灉鏈夋暟瀛﹀叕寮忥紝璇峰姟蹇呬娇鐢?LaTeX 鏁板鐜涔﹀啓銆?

銆愭暟瀛︿笌鍏紡涔﹀啓瑙勮寖銆?

- 鎵€鏈夌墿鐞嗗叕寮忋€佹暟瀛﹀叧绯汇€佸彉閲忓畾涔夛紝蹇呴』浣跨敤鏍囧噯 LaTeX 鏁板鐜涔﹀啓銆?
- 琛屽唴鍏紡璇蜂娇鐢?$...$锛岃闂村叕寮忚浣跨敤 $$...$$銆?
- 绂佹浣跨敤绾枃鏈垨 ASCII 鏂瑰紡琛ㄨ揪鍏紡锛堜緥濡傦細B^2, ~, 鈮? sqrt(), /锛夈€?
- 绂佹浣跨敤鏈畾涔夌殑鑷畾涔夊畯锛堝 \ket, \bra锛夛紝璇蜂娇鐢ㄦ爣鍑?LaTeX 琛ㄨ揪銆?
- 鎵€鏈夌墿鐞嗛噺銆佸悜閲忋€佸紶閲忚浣跨敤 LaTeX 鍛戒护锛堝 \mathbf{k}, \boldsymbol{\sigma}锛夈€?
- 鍏紡灏嗛€氳繃 pandoc + xelatex 缂栬瘧锛屽繀椤讳繚璇佽娉曞彲缂栬瘧銆?
"""

# 瀹屾暣 schema
LLM_SUMMARY_SCHEMA = {
    "name": "condmat_paper_summary_full",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "quick_summary": {
                "type": "object",
                "properties": {
                    "zh": {"type": "string"},
                    "en": {"type": "string"}
                },
                "required": ["zh", "en"]
            },
            "background": {
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
                    "high_level": {
                        "type": "object",
                        "properties": {
                            "zh": {"type": "string"},
                            "en": {"type": "string"}
                        },
                        "required": ["zh", "en"]
                    },
                },
                "required": ["high_level"]
            },
            "experiment_or_application": {
                "type": "object",
                "properties": {
                    "mentioned": {"type": "boolean"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "scenario": {
                                    "type": "object",
                                    "properties": {
                                        "zh": {"type": "string"},
                                        "en": {"type": "string"}
                                    },
                                    "required": ["zh", "en"]
                                },
                                "observable_or_signal": {
                                    "type": "object",
                                    "properties": {
                                        "zh": {"type": "string"},
                                        "en": {"type": "string"}
                                    },
                                    "required": ["zh", "en"]
                                },
                                "platform": {
                                    "type": "object",
                                    "properties": {
                                        "zh": {"type": "string"},
                                        "en": {"type": "string"}
                                    },
                                    "required": ["zh", "en"]
                                }
                            },
                            "required": [
                                "scenario",
                                "observable_or_signal",
                                "platform"
                            ]
                        }
                    }
                },
                "required": ["mentioned", "items"]
            },
            "innovations": {
                "type": "object",
                "properties": {
                    "zh": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "en": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["zh", "en"]
            },
            "prior_work_and_relation": {
                "type": "object",
                "properties": {
                    "zh": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "en": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["zh", "en"]
            },
            "assumptions_and_validity": {
                "type": "object",
                "properties": {
                    "key_assumptions": {
                        "type": "object",
                        "properties": {
                            "zh": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "en": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["zh", "en"]
                    },
                    "valid_regimes": {
                        "type": "object",
                        "properties": {
                            "zh": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "en": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["zh", "en"]
                    },
                    "failure_modes_or_limits": {
                        "type": "object",
                        "properties": {
                            "zh": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "en": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["zh", "en"]
                    }
                },
                "required": [
                    "key_assumptions",
                    "valid_regimes",
                    "failure_modes_or_limits"
                ]
            },
            "physical_insight": {
                "type": "object",
                "properties": {
                    "intuition": {
                        "type": "object",
                        "properties": {
                            "zh": {"type": "string"},
                            "en": {"type": "string"}
                        },
                        "required": ["zh", "en"]
                    },
                    "what_changes_in_understanding": {
                        "type": "object",
                        "properties": {
                            "zh": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "en": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["zh", "en"]
                    }
                },
                "required": ["intuition", "what_changes_in_understanding"]
            },
            "open_questions_and_future": {
                "type": "object",
                "properties": {
                    "zh": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "en": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["zh", "en"]
            },
            "journal_positioning": {
                "type": "object",
                "properties": {
                    "suggested_journals": {
                        "type": "array",
                        "items": {
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
                        }
                    }
                },
                "required": ["suggested_journals"]
            }
        },
        "required": [
            "quick_summary",
            "background",
            "problem",
            "approach",
            "experiment_or_application",
            "innovations",
            "prior_work_and_relation",
            "assumptions_and_validity",
            "physical_insight",
            "open_questions_and_future",
            "journal_positioning"
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
    鍏煎妯″瀷鍋跺皵杈撳嚭 ```json ... ``` 鎴栧す鏉傚皯閲忔枃瀛楃殑鎯呭喌銆?
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


def call_llm_json(paper_text: str, *, use_schema: bool = True) -> dict:
    """
    鍏堝皾璇?response_format=json_schema锛堟湁鏃朵腑杞笉鏀寔浼?400锛?
    濡傛灉閬囧埌 response_format 鐩稿叧 400锛屽垯鑷姩闄嶇骇涓虹函 JSON 妯″紡锛坧rompt 寮虹害鏉?+ 鏈湴 json.loads锛夈€?
    """
    user_msg = "涓嬮潰鏄鏂囧叏鏂囨枃鏈紝璇峰熀浜庡叏鏂囪緭鍑?JSON锛歕n\n" + paper_text

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
            return json.loads(resp.choices[0].message.content)
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
            {"role": "user", "content": "璇蜂弗鏍煎彧杈撳嚭涓€涓?JSON 瀵硅薄锛屼笉瑕佷换浣曡В閲婃枃瀛楋紝涓嶈 markdown 浠ｇ爜鍧椼€俓n\n" + user_msg},
        ],
        temperature=0.2,
    )
    raw = resp.choices[0].message.content
    return json.loads(_extract_first_json_object(raw))


def build_fix_prompt(original_output: dict, errors: list[str], allowed_fields: list[str]) -> str:
    err_block = "\n".join(f"- {e}" for e in errors)
    return f"""
浣犵殑涓婁竴鐗?JSON 杈撳嚭鏈€氳繃 schema 鏍￠獙銆?

銆愬悎娉曢《灞傚瓧娈靛悕浠呴檺浠ヤ笅杩欎簺锛堜笉寰楁柊澧炪€佷笉寰楁敼鍚嶏級銆戯細
{allowed_fields}

銆愭牎楠岄敊璇紙璺緞: 鍘熷洜锛夈€戯細
{err_block}

銆愪綘涓婁竴鐗堢殑瀹屾暣杈撳嚭銆戯細
{json.dumps(original_output, ensure_ascii=False, indent=2)}

璇蜂綘鏍规嵁閿欒鍘熷洜淇 JSON锛屼娇鍏朵弗鏍肩鍚?schema銆?
瑕佹眰锛?
- 杈撳嚭蹇呴』鏄竴涓畬鏁?JSON
- 涓嶈鏂板浠讳綍瀛楁锛涗笉瑕佹敼瀛楁鍚嶏紱涓嶈杈撳嚭瑙ｉ噴鏂囧瓧
鍙緭鍑?JSON銆?
""".strip()


def extract_with_one_fix_retry(paper_text: str) -> dict:
    """
    浣犳兂瑕佺殑閫昏緫锛?
    - 绗竴娆＄敓鎴愬苟鏍￠獙
    - 涓嶉€氳繃锛氭妸閿欒鍘熷洜鍙戠粰 LLM 鍐嶇敓鎴愪竴娆?
    - 浠嶄笉閫氳繃锛氬け璐?
    """
    global SCHEMA_MODE_ENABLED
    allowed_fields = list(LLM_SUMMARY_SCHEMA["schema"]["properties"].keys())

    out1 = call_llm_json(paper_text, use_schema=True)
    errors1 = validate_json_against_schema(out1, LLM_SUMMARY_SCHEMA)
    if not errors1:
        return out1

    fix_prompt = build_fix_prompt(out1, errors1, allowed_fields)

    # 绗簩娆★細渚濇棫鍏堝皾璇?schema锛屽鏋滀笉鏀寔浼氶檷绾?
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
                {"role": "user", "content": "Output one JSON object only, no markdown, no explanations.\n\n" + fix_prompt},
            ],
            temperature=0.1,
        )
        out2 = json.loads(_extract_first_json_object(resp.choices[0].message.content))

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
    璺宠繃宸插畬鎴愮殑锛歴ummarized_at 瀛樺湪涓旈潪绌?
    """
    prov = meta.get("provenance", {})
    return bool(prov.get("summarized_at"))


def process_one_meta(meta_json_path: Path) -> dict:
    """
    杩斿洖锛氱粨鏋?dict锛堢敤浜庢眹鎬绘墦鍗?鍐欐棩蹇楋級
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

        # 灏忛殢鏈烘姈鍔紝闄嶄綆骞跺彂鏃舵挒鍒板悓涓€鍚庣鐨勬鐜?
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

    # 鍐欎竴浠借繍琛屾棩蹇楋紝鏂逛究浣犲洖鐪嬪け璐ュ師鍥?
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

    # 鏂板锛氬け璐ュ惊鐜噸璺戞帶鍒?
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

    # attempt 璁℃暟锛氶槻姝㈡煇浜涙案涔呭け璐ュ鑷存寰幆
    attempts: dict[str, int] = {p.name: 0 for p in meta_files_all}

    # 绗竴杞細璺戝叏閮紱鍚庣画杞锛氬彧璺戝け璐?
    pending = meta_files_all[:]
    all_results = []  # 淇濆瓨姣忔鎵ц鐨勭粨鏋滐紙鍖呭惈杞淇℃伅锛?

    round_idx = 1
    while pending and round_idx <= args.max_rounds:
        print(f"\n[ROUND {round_idx}] pending={len(pending)}")
        round_results = []

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {}
            for p in pending:
                if attempts[p.name] >= args.max_attempts_per_file:
                    # 宸茶揪鍒版渶澶у皾璇曟鏁帮紝鐩存帴鏍囪涓?fail锛屼笉鍐嶆彁浜?
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

        # 璁＄畻涓嬩竴杞閲嶈窇鐨勬枃浠讹細鍙噸璺?fail锛屼笖娌¤秴杩?max_attempts_per_file
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

    # 鏈€缁堢粺璁?
    final_ok = sum(1 for r in all_results if r["status"] == "ok")
    final_skipped = sum(1 for r in all_results if r["status"] == "skipped")

    # 娉ㄦ剰锛氫竴涓枃浠跺彲鑳藉娆?fail 鍚庢垚鍔燂紝鎵€浠ユ渶缁?fail 闇€瑕佹寜鈥滄渶鍚庝竴娆＄姸鎬佲€濈粺璁℃洿鍚堢悊
    # 杩欓噷缁欏嚭鈥滀粛鏈垚鍔熶笖杈惧埌涓婇檺/杞鐢ㄥ敖鈥濈殑鏂囦欢鏁伴噺
    last_status = {}
    for r in all_results:
        last_status[r["file"]] = r["status"]

    still_fail = sum(1 for f, st in last_status.items() if st == "fail")

    print("-" * 80)
    print(f"Done. ok={final_ok}, skipped={final_skipped}, still_fail={still_fail}, rounds={round_idx if all_results else 0}")

    # 鍐欒繍琛屾棩蹇楋紙鍖呭惈姣忚疆/姣忔 attempt锛?
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

