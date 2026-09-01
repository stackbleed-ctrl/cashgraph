from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from cashgraph.models import Extracted, PiggybackHit
from cashgraph.universe import is_illiquid, is_mega, load_universe


def detect_piggybacks(
    items: list[Extracted],
    universe=None,
    min_authors: int = 2,
) -> list[PiggybackHit]:
    """Flag illiquid/unknown tickers co-mentioned with mega hosts."""
    universe = universe or load_universe()
    pair_posts: dict[tuple[str, str], int] = defaultdict(int)
    pair_authors: dict[tuple[str, str], set[str]] = defaultdict(set)

    for it in items:
        tags = sorted(set(it.cashtags))
        if len(tags) < 2:
            continue
        for a, b in combinations(tags, 2):
            pair_posts[(a, b)] += 1
            pair_authors[(a, b)].add(it.post.author_id)

    hits: list[PiggybackHit] = []
    seen: set[tuple[str, str]] = set()
    for (a, b), posts in pair_posts.items():
        authors = len(pair_authors[(a, b)])
        if authors < min_authors:
            continue
        for host, parasite in ((a, b), (b, a)):
            if not is_mega(host, universe):
                continue
            if not is_illiquid(parasite, universe):
                continue
            key = (host, parasite)
            if key in seen:
                continue
            seen.add(key)
            # higher score = more suspicious hitchhiking
            score = authors * 2.0 + posts * 0.5
            if is_illiquid(parasite, universe) and parasite not in universe:
                score += 3.0
                reason = "unknown ticker riding mega cashtag"
            else:
                reason = "illiquid ticker co-mentioned with mega cashtag"
            hits.append(
                PiggybackHit(
                    host=host,
                    parasite=parasite,
                    co_posts=posts,
                    unique_authors=authors,
                    score=round(score, 2),
                    reason=reason,
                )
            )
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits
