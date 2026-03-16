import argparse
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]

load_dotenv()


def _env(name: str, *, required: bool = True, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value or ""


def _collect_attachments(run_date: str) -> list[Path]:
    candidates = [
        ROOT / "reports" / "zh" / f"{run_date}_daily_llm_report_zh.pdf",
        ROOT / "reports" / "en" / f"{run_date}_daily_llm_report_en.pdf",
        ROOT / "reports" / "log" / f"{run_date}_daily_llm_report_zh.md",
        ROOT / "reports" / "log" / f"{run_date}_daily_llm_report_en.md",
    ]
    return [path for path in candidates if path.exists()]


def _attach_files(message: EmailMessage, files: Iterable[Path]) -> None:
    for path in files:
        data = path.read_bytes()
        if path.suffix.lower() == ".pdf":
            maintype, subtype = "application", "pdf"
        else:
            maintype, subtype = "text", "markdown"
        message.add_attachment(data, maintype=maintype, subtype=subtype, filename=path.name)


def send_report_email(run_date: str) -> list[Path]:
    smtp_host = _env("SMTP_HOST")
    smtp_port = int(_env("SMTP_PORT"))
    smtp_user = _env("SMTP_USER")
    smtp_password = _env("SMTP_PASSWORD")
    email_to = _env("EMAIL_TO")
    email_from = _env("EMAIL_FROM", required=False, default=smtp_user)
    subject_prefix = _env("EMAIL_SUBJECT_PREFIX", required=False, default="[Paper Scout]")

    attachments = _collect_attachments(run_date)

    message = EmailMessage()
    if attachments:
        subject = f"{subject_prefix} {run_date} Daily Paper Digest"
    else:
        subject = f"{subject_prefix} {run_date} No New Report"

    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = email_to
    if attachments:
        message.set_content(
            "\n".join(
                [
                    f"Paper Scout report for {run_date} is attached.",
                    "",
                    "Included files:",
                    *[f"- {path.name}" for path in attachments],
                ]
            )
        )
        _attach_files(message, attachments)
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

    return attachments


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "date",
        nargs="?",
        default=datetime.now().date().isoformat(),
        help="YYYY-MM-DD (default=today)",
    )
    args = parser.parse_args()

    attachments = send_report_email(args.date)
    if attachments:
        print(f"Email sent with {len(attachments)} attachment(s).")
        for path in attachments:
            print(f" - {path}")
    else:
        print("Email sent without attachments because no report files were generated.")


if __name__ == "__main__":
    main()
