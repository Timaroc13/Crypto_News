from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_golden_cases(path: Path) -> list[dict[str, Any]]:
    """Load golden cases from a file.

    Supported formats:
    - JSONL: one JSON object per line
    - JSON text sequence: multiple JSON objects concatenated with whitespace/newlines
    - JSON array: a single JSON array of objects
    """

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    first = text.lstrip()[:1]
    if first == "[":
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("golden cases JSON array must be a list")
        return [c for c in data if isinstance(c, dict)]

    # Attempt JSONL first: if every non-empty line is standalone JSON.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and all(line.startswith("{") and line.endswith("}") for line in lines):
        cases: list[dict[str, Any]] = []
        for line in lines:
            obj = json.loads(line)
            if isinstance(obj, dict):
                cases.append(obj)
        return cases

    # Fallback: parse as a JSON text sequence (multiple objects, pretty-printed).
    decoder = json.JSONDecoder()
    idx = 0
    cases = []
    while idx < len(text):
        # Skip whitespace
        while idx < len(text) and text[idx].isspace():
            idx += 1
        if idx >= len(text):
            break

        obj, next_idx = decoder.raw_decode(text, idx)
        if isinstance(obj, dict):
            cases.append(obj)
        idx = next_idx

    return cases
