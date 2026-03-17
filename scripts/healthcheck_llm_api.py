import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def main() -> None:
    api_key = _env("MY_API_KEY")
    base_url = _env("MY_API_BASE_URL", "https://api1.uiuiapi.com/v1")
    model = _env("LLM_MODEL", "gemini-3-flash-preview")

    if not api_key:
        raise RuntimeError("Missing MY_API_KEY in .env")

    client = OpenAI(api_key=api_key, base_url=base_url)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "Reply with exactly: ok"},
        ],
        temperature=0,
        max_tokens=5,
    )

    content = (resp.choices[0].message.content or "").strip()
    print("Healthcheck response:", content)
    if "ok" not in content.lower():
        raise RuntimeError(f"Unexpected healthcheck response: {content!r}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Healthcheck failed: {exc}", file=sys.stderr)
        raise
