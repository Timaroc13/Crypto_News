from __future__ import annotations

from collections import Counter
from pathlib import Path

from crypto_news_parser.golden import load_golden_cases


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "eval" / "golden_cases.jsonl"
    cases = load_golden_cases(path)

    labels = Counter()
    v1_labels = Counter()
    jurs = Counter()
    v1_jurs = Counter()

    for c in cases:
        exp = c.get("expected", {}) or {}
        if et := exp.get("event_type"):
            labels[et] += 1
        if v1 := exp.get("v1_event_type"):
            v1_labels[v1] += 1
        if j := exp.get("jurisdiction"):
            jurs[j] += 1
        if v1j := exp.get("v1_jurisdiction"):
            v1_jurs[v1j] += 1

    print(f"cases: {len(cases)}")

    print("\nTop expected.event_type labels:")
    for k, v in labels.most_common(50):
        print(f"  {k}: {v}")

    print("\nTop expected.v1_event_type labels:")
    for k, v in v1_labels.most_common(50):
        print(f"  {k}: {v}")

    print("\nTop expected.jurisdiction labels:")
    for k, v in jurs.most_common(50):
        print(f"  {k}: {v}")

    print("\nTop expected.v1_jurisdiction labels:")
    for k, v in v1_jurs.most_common(50):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
