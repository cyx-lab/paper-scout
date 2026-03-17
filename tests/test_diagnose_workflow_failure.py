from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from scripts.diagnose_workflow_failure import diagnose_log


def main() -> None:
    sample_502 = """
    [ROUND 1] pending=8
    [RETRY] transient API error code=502 (attempt 1/5), sleep=1.6s
    [FAIL] 2603.14800v1.json
    Error code: 502 - {'error': {'message': 'Service temporarily unavailable', 'type': 'service_error'}}
    """
    out_502 = diagnose_log(sample_502)
    assert out_502 and out_502[0].key == "upstream_502", out_502

    sample_escape = r"""
    [FAIL] 2603.14996v1.json
    Invalid \escape: line 73 column 208 (char 3106)
    """
    out_escape = diagnose_log(sample_escape)
    assert any(item.key == "invalid_escape" for item in out_escape), out_escape

    sample_fetch0 = """
    Fetched: 0 papers
    No meta json files found under: /tmp/project/data/pdfs/2026-03-16/json
    """
    out_fetch0 = diagnose_log(sample_fetch0)
    assert any(item.key == "no_papers_fetched" for item in out_fetch0), out_fetch0

    print("OK: workflow diagnosis patterns are recognized.")


if __name__ == "__main__":
    main()
