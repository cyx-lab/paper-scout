from pathlib import Path
import os
import types
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

os.environ.setdefault("MY_API_KEY", "test-key")


class _DummyCompletions:
    def create(self, **kwargs):
        raise RuntimeError("LLM call should not happen in schema/render test")


class _DummyChat:
    def __init__(self):
        self.completions = _DummyCompletions()


class _DummyOpenAI:
    def __init__(self, *args, **kwargs):
        self.chat = _DummyChat()


sys.modules.setdefault("openai", types.SimpleNamespace(OpenAI=_DummyOpenAI))

from scripts.fetch_with_json import empty_bilingual_summary
from scripts.generate_daily_reports_bilingual import render_paper
from scripts.run_daily_summaries import LLM_SUMMARY_SCHEMA
from src.llm.schema_checker import validate_json_against_schema


def build_sample_meta() -> dict:
    summary = empty_bilingual_summary()
    summary["one_sentence_summary"] = {
        "zh": "本文研究扭转双层体系中的激子输运，并提炼出一个适合日报速读的简短结论。",
        "en": "This paper studies exciton transport in a twisted bilayer system and distills the result into a digest-friendly summary.",
    }
    summary["problem"] = {
        "zh": "作者要回答扭转结构如何改变激子扩散与相干输运。",
        "en": "The authors ask how twist modifies exciton diffusion and coherent transport.",
    }
    summary["approach"] = {
        "zh": "结合有效模型与数值模拟比较不同扭转角下的输运行为。",
        "en": "The work combines an effective model with numerical simulations across different twist angles.",
    }
    summary["main_takeaway"] = {
        "zh": "核心 takeaway 是扭转角可以显著重排输运通道，并形成清晰的角度依赖趋势。",
        "en": "The main takeaway is that the twist angle can reorganize transport channels and create a clear angle-dependent trend.",
    }
    summary["why_it_matters"] = {
        "zh": "这为理解 moire 激子器件中的可调输运提供了直接线索。",
        "en": "This offers a direct clue for tunable transport in moire excitonic devices.",
    }
    summary["value_assessment"] = {
        "level": {"zh": "重要进展", "en": "Major advance"},
        "reason": {
            "zh": "这项工作对一个具体物理问题给出了清楚且有说服力的新结论。",
            "en": "The work delivers a clear and persuasive new result on a concrete physics question.",
        },
    }
    summary["paper_type"] = {"zh": "理论 + 数值", "en": "Theory + numerics"}
    summary["likely_venue"] = {
        "journal": "Physical Review Letters",
        "confidence": "medium",
        "reason": {
            "zh": "工作强调普适物理机制，结论简洁，叙事风格接近快报型期刊。",
            "en": "The paper emphasizes a compact physical mechanism and has a concise letter-style narrative.",
        },
    }
    summary["keywords"] = ["moire", "exciton transport", "twisted bilayer", "condensed matter"]

    return {
        "paper_record": {
            "id": "2603.12345v1",
            "title": "Mock condensed matter digest paper",
            "authors": ["Alice Example", "Bob Example"],
            "categories": ["cond-mat.str-el"],
            "signals": {
                "rule_score": 7,
                "keyword_hits": ["moire", "exciton"],
            },
        },
        "assets": {
            "pdf_path": "data/pdfs/2026-03-17/mock.pdf",
            "pdf_url": "https://arxiv.org/pdf/2603.12345v1.pdf",
        },
        "provenance": {"summarized_at": "2026-03-17T10:00:00"},
        "llm_summary": summary,
    }


def main() -> None:
    summary = empty_bilingual_summary()
    errors = validate_json_against_schema(summary, LLM_SUMMARY_SCHEMA)
    if errors:
        raise AssertionError(f"Empty summary should match schema, got: {errors}")

    meta = build_sample_meta()
    errors = validate_json_against_schema(meta["llm_summary"], LLM_SUMMARY_SCHEMA)
    if errors:
        raise AssertionError(f"Sample summary should match schema, got: {errors}")

    zh_report = render_paper(meta, 7.0, "zh")
    en_report = render_paper(meta, 7.0, "en")

    expected_zh = ["一句话摘要", "核心 takeaway", "价值等级评估", "可能投稿去向", "Physical Review Letters", "moire"]
    expected_en = ["One-sentence summary", "Main takeaway", "Value assessment", "Likely venue", "Physical Review Letters", "moire"]

    for token in expected_zh:
        if token not in zh_report:
            raise AssertionError(f"Missing token in zh render: {token}")
    for token in expected_en:
        if token not in en_report:
            raise AssertionError(f"Missing token in en render: {token}")

    print("OK: digest schema and rendering are aligned.")


if __name__ == "__main__":
    main()
