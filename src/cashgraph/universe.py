from __future__ import annotations

import json
from pathlib import Path

from cashgraph.models import Asset

DEFAULT_UNIVERSE = Path(__file__).resolve().parents[2] / "data" / "universe.json"


def load_universe(path: Path | None = None) -> dict[str, Asset]:
    p = path or DEFAULT_UNIVERSE
    raw = json.loads(p.read_text())
    out: dict[str, Asset] = {}
    for item in raw["assets"]:
        a = Asset(**item)
        a.cashtag = a.cashtag.upper().lstrip("$")
        out[a.cashtag] = a
    return out


def is_mega(tag: str, universe: dict[str, Asset]) -> bool:
    a = universe.get(tag.upper())
    return bool(a and a.mega)


def is_illiquid(tag: str, universe: dict[str, Asset]) -> bool:
    a = universe.get(tag.upper())
    if a:
        return a.illiquid
    # unknown ticker treated as potential parasite
    return True
