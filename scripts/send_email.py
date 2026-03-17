import argparse
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]

load_dotenv()


def _env(name: str, *, required: bool = True, default: str | None = None) -> str:
    value = os.getenv(name)
    if value is not None:
        value = value.strip()
    if not value:
        value = default
    if required and not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value or ""


def _read_report_bodies(run_date: str) -> tuple[str, str]:
    zh_path = ROOT / "reports" / "log" / f"{run_date}_daily_llm_report_zh.md"
    en_path = ROOT / "reports" / "log" / f"{run_date}_daily_llm_report_en.md"

    zh_body = zh_path.read_text(encoding="utf-8") if zh_path.exists() else ""
    en_body = en_path.read_text(encoding="utf-8") if en_path.exists() else ""
    return zh_body.strip(), en_body.strip()


def send_report_email(run_date: str) -> bool:
    smtp_host = _env("SMTP_HOST")
    smtp_port = int(_env("SMTP_PORT"))
    smtp_user = _env("SMTP_USER")
    smtp_password = _env("SMTP_PASSWORD")
    email_to = _env("EMAIL_TO")
    email_from = _env("EMAIL_FROM", required=False, default=smtp_user)
    subject_prefix = _env("EMAIL_SUBJECT_PREFIX", required=False, default="[Paper Scout]")

    zh_body, en_body = _read_report_bodies(run_date)
    has_report = bool(zh_body or en_body)

    message = EmailMessage()
    if has_report:
        subject = f"{subject_prefix} {run_date} Daily Paper Digest"
    else:
        subject = f"{subject_prefix} {run_date} No New Report"

    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = email_to
    if has_report:
        body_parts = []
        if zh_body:
            body_parts.extend(
                [
                    f"Paper Scout digest for {run_date}",
                    "",
                    "===== 中文 =====",
                    "",
                    zh_body,
                ]
            )
        if en_body:
            if body_parts:
                body_parts.extend(["", "", "===== English =====", ""])
            else:
                body_parts.extend(
                    [
                        f"Paper Scout digest for {run_date}",
                        "",
                        "===== English =====",
                        "",
                    ]
                )
            body_parts.append(en_body)

        message.set_content(
            "\n".join(body_parts).strip() + "\n"
        )
    else:
        message.set_content(
            "\n".join(
                [
                    f"Paper Scout ran successfully on {run_date}, but no daily report files were generated.",
                    "",
                    "Possible reasons:",
                    "- No new papers were fetched in the configured categories/time window.",
                    "- No papers passed downstream processing.",
                ]
            )
        )

    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.send_message(message)

    return has_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "date",
        nargs="?",
        default=datetime.now().date().isoformat(),
        help="YYYY-MM-DD (default=today)",
    )
    args = parser.parse_args()

    has_report = send_report_email(args.date)
    if has_report:
        print("Email sent with digest content in the message body.")
    else:
        print("Email sent without report content because no daily report files were generated.")


if __name__ == "__main__":
    main()
