from __future__ import annotations

import re

# $BRK.B, $BTC-USD, $SPX, reject $123.45 and lone $
_CASHTAG = re.compile(
    r"(?<![A-Za-z0-9_])\$([A-Za-z][A-Za-z0-9]{0,9}(?:[.-][A-Za-z0-9]{1,4})?)\b"
)

_STOP = {
    "USD",
    "CASH",
    "MONEY",
    "PRICE",
    "AND",
    "THE",
    "FOR",
    "NOT",
}


def extract_cashtags(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in _CASHTAG.finditer(text or ""):
        tag = m.group(1).upper()
        if tag in _STOP:
            continue
        if tag not in seen:
            seen.add(tag)
            found.append(tag)
    return found
