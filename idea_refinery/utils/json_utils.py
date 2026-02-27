from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass
class JSONParseError(Exception):
    message: str
    raw: str


def extract_json(text: str) -> str | None:
    if not text:
        return None
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else None


def parse_json(text: str) -> object:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        extracted = extract_json(text)
        if extracted:
            try:
                return json.loads(extracted)
            except json.JSONDecodeError as exc:
                raise JSONParseError(str(exc), text) from exc
        raise JSONParseError("No JSON object found", text)
