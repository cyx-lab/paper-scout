import sys

# Avoid Windows GBK console crashes when downstream scripts print Unicode.
for stream_name in ("stdout", "stderr"):
    stream = getattr(sys, stream_name, None)
    if stream and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from scripts.fetch_with_json import fetch_and_process
from scripts.generate_daily_reports_bilingual import generate_daily_reports
from scripts.run_daily_summaries import run_summaries

def run_all():
    print("Starting fetch and process...")
    fetch_and_process()
    print("Fetch and process completed.")

    print("Starting daily summaries...")
    run_summaries()
    print("Daily summaries completed.")

    print("Starting daily report generation...")
    generate_daily_reports()
    print("Daily report generation completed.")
    return

if __name__ == "__main__":
    run_all()
