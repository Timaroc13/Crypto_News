from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_news_parser.storage import export_feedback_cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Export stored feedback as eval-compatible JSONL")
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[1] / "eval" / "feedback_cases.jsonl"),
        help="Output path for JSONL",
    )
    args = parser.parse_args()

    cases = export_feedback_cases()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        for obj in cases:
            f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(f"exported: {len(cases)}")
    print(f"path: {out_path}")


if __name__ == "__main__":
    main()
