# src/llm/schema_checker.py

from typing import List, Tuple
from jsonschema import Draft202012Validator


def validate_json_against_schema(
    data: dict,
    schema: dict
) -> List[str]:
    """
    严格校验 JSON 是否符合 schema

    返回：
        errors: List[str]
        - 空列表 => 校验通过
        - 非空 => 每一条是一个可读错误
    """
    validator = Draft202012Validator(schema["schema"])
    errors: List[str] = []

    for err in validator.iter_errors(data):
        # err.absolute_path 是一个 deque
        if err.absolute_path:
            path = ".".join(str(p) for p in err.absolute_path)
            errors.append(f"{path}: {err.message}")
        else:
            # 根级错误（例如缺失 required / 多余字段）
            errors.append(err.message)

    return errors


def extract_allowed_top_level_fields(schema: dict) -> List[str]:
    """
    提取 schema 允许的顶层字段名（用于 repair 提示）
    """
    return list(schema["schema"]["properties"].keys())




# =================================================
# Debug / self-test
# =================================================
if __name__ == "__main__":

    # -----------------------------
    # 一个最小但合理的 schema（测试用）
    # -----------------------------
    TEST_SCHEMA = {
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
                    "required": ["zh", "en"],
                    "additionalProperties": False
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
                    "required": ["zh", "en"],
                    "additionalProperties": False
                }
            },
            "required": ["quick_summary", "open_questions_and_future"]
        }
    }

    # -----------------------------
    # 正确示例（应当通过）
    # -----------------------------
    GOOD_EXAMPLE = {
        "quick_summary": {
            "zh": "本文研究了量子几何在能带拓扑中的作用。",
            "en": "This paper studies the role of quantum geometry in band topology."
        },
        "open_questions_and_future": {
            "zh": ["相互作用效应如何影响结论？"],
            "en": ["How do interactions affect the conclusions?"]
        }
    }

    # -----------------------------
    # 错误示例（应当失败）
    # -----------------------------
    BAD_EXAMPLE = {
        "quick_summary": {
            "zh": "这是摘要",
            "en": "This is a summary"
        },

        # ❌ 字段名错误
        "open_question": {
            "zh": ["未来问题"],
            "en": ["Future questions"]
        },

        # ❌ 多余字段
        "extra_field": "should not be here"
    }

    # -----------------------------
    # Run tests
    # -----------------------------
    def run_case(name: str, data: dict):
        print("=" * 80)
        print(f"TEST CASE: {name}")
        print("-" * 80)
        errors = validate_json_against_schema(data, TEST_SCHEMA)
        if not errors:
            print("✅ PASSED schema validation")
        else:
            print("❌ FAILED schema validation")
            for e in errors:
                print(" -", e)

    run_case("GOOD_EXAMPLE (should pass)", GOOD_EXAMPLE)
    run_case("BAD_EXAMPLE (should fail)", BAD_EXAMPLE)