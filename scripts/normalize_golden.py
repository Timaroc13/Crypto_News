from __future__ import annotations

import json
from pathlib import Path

from crypto_news_parser.golden import load_golden_cases
from crypto_news_parser.models import EventTypeV1, Jurisdiction


def map_to_v1_event_type(label: str | None, text: str) -> str:
    if not label:
        return EventTypeV1.UNKNOWN.value

    # If it's already a v1 enum value, keep it.
    if label in {e.value for e in EventTypeV1}:
        return label

    label_upper = label.upper()
    t = text.lower()

    # Conservative mappings: only map when clearly equivalent.
    if "STABLECOIN" in label_upper and any(
        k in t for k in ["issu", "mint", "launched", "registered", "backed"]
    ):
        return EventTypeV1.STABLECOIN_ISSUANCE.value

    if (
        "DEPEG" in label_upper
        or "DEPEG" in t.upper()
        or "lost its peg" in t
        or "trading below $1" in t
    ):
        return EventTypeV1.STABLECOIN_DEPEG.value

    if any(k in label_upper for k in ["HACK", "EXPLOIT", "BREACH"]):
        return EventTypeV1.EXCHANGE_HACK.value

    if any(
        k in label_upper
        for k in ["ETF_APPROVAL", "ETF_REJECTION", "ETF_FILING", "ETF_INFLOW", "ETF_OUTFLOW"]
    ):
        # If they used a custom but close ETF label, attempt to match.
        for et in [
            EventTypeV1.ETF_APPROVAL,
            EventTypeV1.ETF_REJECTION,
            EventTypeV1.ETF_FILING,
            EventTypeV1.ETF_INFLOW,
            EventTypeV1.ETF_OUTFLOW,
        ]:
            if et.value in label_upper:
                return et.value

    # Enforcement-ish labels are often ambiguous (guidance vs action); keep UNKNOWN for now.
    return EventTypeV1.UNKNOWN.value


def map_to_v1_jurisdiction(label: str | None) -> str:
    if not label:
        return Jurisdiction.GLOBAL.value

    if label in {j.value for j in Jurisdiction}:
        return label

    # Minimal conservative mapping.
    u = label.upper()
    if u in {"USA", "UNITED_STATES", "U.S.", "US"}:
        return Jurisdiction.US.value

    # Map common country/city labels to continent buckets.
    if u in {"UAE", "SAUDI_ARABIA", "QATAR", "ISRAEL", "TURKEY"}:
        return Jurisdiction.ASIA.value

    if u in {"HONG_KONG", "SINGAPORE", "JAPAN", "CHINA", "KOREA", "INDIA"}:
        return Jurisdiction.ASIA.value

    if u in {"RUSSIA"}:
        return Jurisdiction.EUROPE.value

    if u in {"UK", "UNITED_KINGDOM", "EU", "GERMANY", "FRANCE", "ITALY", "SPAIN"}:
        return Jurisdiction.EUROPE.value

    if u in {"CANADA", "MEXICO", "BRAZIL", "ARGENTINA"}:
        return Jurisdiction.AMERICAS_NON_US.value

    return Jurisdiction.GLOBAL.value


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "eval" / "golden_cases.jsonl"

    cases = load_golden_cases(path)
    changed = 0

    for c in cases:
        expected = c.setdefault("expected", {})
        if not isinstance(expected, dict):
            continue

        if "v1_event_type" not in expected:
            expected["v1_event_type"] = map_to_v1_event_type(
                expected.get("event_type"),
                c.get("text", ""),
            )
            changed += 1

        if "v1_jurisdiction" not in expected and "jurisdiction" in expected:
            expected["v1_jurisdiction"] = map_to_v1_jurisdiction(expected.get("jurisdiction"))
            changed += 1

    # Write as pretty JSON text sequence (multiple objects back-to-back),
    # to match the current file style.
    out = "\n".join(json.dumps(c, ensure_ascii=False, indent=2) for c in cases) + "\n"
    path.write_text(out, encoding="utf-8")

    print(f"Updated {changed} fields across {len(cases)} cases")


if __name__ == "__main__":
    main()
