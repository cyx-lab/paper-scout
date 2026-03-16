import json
import time
from jsonschema import Draft202012Validator

def validate_json_against_schema(data: dict, schema: dict) -> list[str]:
    """
    返回错误列表；空列表表示通过
    """
    validator = Draft202012Validator(schema["schema"])
    errors = []
    for err in validator.iter_errors(data):
        if err.absolute_path:
            path = ".".join(str(p) for p in err.absolute_path)
            errors.append(f"{path}: {err.message}")
        else:
            errors.append(err.message)
    return errors


def build_fix_prompt(original_output: dict, errors: list[str], allowed_fields: list[str]) -> str:
    """
    把错误原因发给 LLM，让它改一版（输出仍需完整 JSON）
    """
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
- 未被错误涉及的字段内容尽量保持不变
只输出 JSON。
""".strip()


def extract_llm_summary_once(paper_text: str, *, client, model: str, system_prompt: str, schema: dict) -> dict:
    """
    你原来的 extract_llm_summary 逻辑（这里抽成一次调用，便于复用）
    """
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "下面是论文全文文本，请基于全文输出 JSON：\n\n" + paper_text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": schema
        },
        temperature=0.2,
    )
    return json.loads(resp.choices[0].message.content)


def extract_with_one_fix_retry(
    paper_text: str,
    *,
    client,
    model: str,
    system_prompt: str,
    schema: dict,
) -> dict:
    """
    你要的策略：
    - 第一次生成，校验
    - 不通过：把 errors 发给 LLM，再生成一次（修复版）
    - 还不通过：失败
    """
    allowed_fields = list(schema["schema"]["properties"].keys())

    # 1) first try
    out1 = extract_llm_summary_once(
        paper_text,
        client=client,
        model=model,
        system_prompt=system_prompt,
        schema=schema,
    )
    errors1 = validate_json_against_schema(out1, schema)
    if not errors1:
        return out1

    # 2) one fix try with errors
    fix_prompt = build_fix_prompt(out1, errors1, allowed_fields)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": fix_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": schema
        },
        temperature=0.1,
    )
    out2 = json.loads(resp.choices[0].message.content)
    errors2 = validate_json_against_schema(out2, schema)
    if not errors2:
        return out2

    # 3) fail
    raise RuntimeError(
        "LLM output failed schema validation after one fix retry.\n"
        "First pass errors:\n- " + "\n- ".join(errors1) + "\n\n"
        "Second pass errors:\n- " + "\n- ".join(errors2)
    )
