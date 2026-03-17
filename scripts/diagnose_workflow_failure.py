import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Diagnosis:
    key: str
    title: str
    cause: str
    evidence: list[str]
    actions: list[str]
    priority: int = 100


def _snippet(pattern: str, text: str, *, flags: int = 0) -> list[str]:
    matches = []
    for m in re.finditer(pattern, text, flags):
        start = max(0, m.start() - 80)
        end = min(len(text), m.end() + 120)
        chunk = text[start:end].strip().replace("\r", "")
        matches.append(chunk)
        if len(matches) >= 3:
            break
    return matches


def diagnose_log(text: str) -> list[Diagnosis]:
    found: list[Diagnosis] = []

    if re.search(r"Error code:\s*502|Service temporarily unavailable", text, re.I):
        found.append(
            Diagnosis(
                key="upstream_502",
                title="上游 LLM 服务临时不可用",
                cause=(
                    "日志显示是 502 / service unavailable。更像是中转或上游模型服务不稳定，"
                    "而不是本地代码逻辑错误。GitHub runner 的网络出口、并发或时间点都可能触发这个问题。"
                ),
                evidence=_snippet(r"Error code:\s*502|Service temporarily unavailable", text, flags=re.I),
                actions=[
                    "先把 `LLM_WORKERS` 降到 1，减少并发压力。",
                    "适当提高 `LLM_MAX_API_RETRIES` 和 `LLM_RETRY_MAX_SLEEP`。",
                    "核对 GitHub Secrets 里的 `MY_API_BASE_URL`、`MY_API_KEY`、`LLM_MODEL` 是否和本地一致。",
                    "如果本地稳定、GitHub 不稳定，优先怀疑服务对 GitHub runner 的网络出口不稳定。",
                ],
                priority=10,
            )
        )

    if re.search(r"Invalid \\escape", text):
        found.append(
            Diagnosis(
                key="invalid_escape",
                title="模型输出了非法 JSON 转义",
                cause=(
                    "这通常不是 PDF 或 pandoc 的问题，而是模型在 JSON 字符串里输出了未正确转义的反斜杠，"
                    "导致 `json.loads` 失败。"
                ),
                evidence=_snippet(r"Invalid \\escape", text),
                actions=[
                    "检查当前 `run_daily_summaries.py` 是否包含 JSON 反斜杠修复逻辑。",
                    "优先避免让 prompt 生成公式或大量带反斜杠的内容。",
                    "若问题反复出现，记录原始模型输出，确认是哪类字段最容易触发。",
                ],
                priority=20,
            )
        )

    if re.search(r"Fetched:\s*0 papers", text) and re.search(r"No meta json files found under:", text):
        found.append(
            Diagnosis(
                key="no_papers_fetched",
                title="当天没有抓到可下游处理的论文",
                cause=(
                    "抓取阶段已经是 0 篇，所以后面的摘要、日报、邮件附件都不会生成。"
                    "这通常是时间窗口、分类范围或当天确实没有新文导致。"
                ),
                evidence=_snippet(r"Fetched:\s*0 papers|No meta json files found under:", text),
                actions=[
                    "检查 `config/profiles/my_phd_config.yaml` 中的分类和时间窗口是否过窄。",
                    "如果你希望日报更稳定每天都有内容，可以适当放宽抓取窗口或分类。",
                    "邮件脚本已支持“无新报告”提示邮件，这类情况不应再导致 workflow 失败。",
                ],
                priority=30,
            )
        )

    if re.search(r"No report files found .* under reports/", text):
        found.append(
            Diagnosis(
                key="missing_report_files",
                title="邮件步骤找不到日报附件",
                cause=(
                    "邮件脚本在发送时没有找到当天的 md/pdf 报告文件。通常根因发生在更前面的抓取或摘要阶段。"
                ),
                evidence=_snippet(r"No report files found .* under reports/", text),
                actions=[
                    "先查看 `Run pipeline` 的日志，不要只盯着 `Email reports`。",
                    "确认当天是否真的生成了 `reports/log/*daily_llm_report*.md` 或 `reports/zh|en/*.pdf`。",
                    "如果你的仓库还是旧版邮件脚本，先更新到当前版本。",
                ],
                priority=40,
            )
        )

    if re.search(r"ModuleNotFoundError: No module named 'httpx'", text):
        found.append(
            Diagnosis(
                key="missing_httpx",
                title="Python 依赖不完整：缺少 httpx",
                cause="`openai` 依赖链需要 `httpx`，当前运行环境没有装全依赖。",
                evidence=_snippet(r"ModuleNotFoundError: No module named 'httpx'", text),
                actions=[
                    "重新安装 `requirements.txt`。",
                    "确认运行时使用的是你想要的 Python 环境，而不是 base Python。",
                    "当前仓库的 `requirements.txt` 已包含 `httpx` 与 `python-dotenv`。",
                ],
                priority=15,
            )
        )

    if re.search(r"Missing environment variable:|Missing API key|Missing API_KEY", text):
        found.append(
            Diagnosis(
                key="missing_env",
                title="缺少必要环境变量或 secret",
                cause="运行环境里没有找到 API key 或 SMTP 相关配置。",
                evidence=_snippet(r"Missing environment variable:|Missing API key|Missing API_KEY", text),
                actions=[
                    "核对本地 `.env` 或 GitHub Secrets 是否已经设置。",
                    "确认 workflow 里注入的 secret 名称和代码读取的环境变量名称一致。",
                ],
                priority=12,
            )
        )

    if re.search(r"pandoc|xelatex|pdf-engine|\.pandoc_stderr\.txt", text, re.I):
        found.append(
            Diagnosis(
                key="pdf_rendering",
                title="PDF 渲染链路异常",
                cause="日志涉及 pandoc / xelatex，问题更可能在 Markdown 转 PDF 阶段。",
                evidence=_snippet(r"pandoc|xelatex|pdf-engine|\.pandoc_stderr\.txt", text, flags=re.I),
                actions=[
                    "检查 `reports/log/*.pandoc_stderr.txt` 是否有更具体错误。",
                    "确认 runner 已安装 `pandoc`、`texlive-xetex` 和中文字体。",
                    "如果只是想保底发送，可先加 `--no-pdf` 验证前面的摘要链路。",
                ],
                priority=50,
            )
        )

    return sorted(found, key=lambda x: x.priority)


def _read_input(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8", errors="replace")

    if not sys.stdin.isatty():
        return sys.stdin.read()

    raise SystemExit("Provide a log file path or pipe log text into stdin.")


def _print_report(items: list[Diagnosis]) -> None:
    if not items:
        print("No known failure pattern matched.")
        print("建议：把完整日志保存成 txt，再用这个脚本重新分析。")
        return

    print("Detected likely causes:\n")
    for idx, item in enumerate(items, 1):
        print(f"{idx}. {item.title}")
        print(f"   Cause: {item.cause}")
        if item.evidence:
            print("   Evidence:")
            for ev in item.evidence:
                print(f"   - {ev}")
        if item.actions:
            print("   Suggested actions:")
            for action in item.actions:
                print(f"   - {action}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diagnose likely causes from GitHub Actions or local pipeline logs."
    )
    parser.add_argument("logfile", nargs="?", help="Path to a log text file. If omitted, read from stdin.")
    args = parser.parse_args()

    text = _read_input(args.logfile)
    _print_report(diagnose_log(text))


if __name__ == "__main__":
    main()
