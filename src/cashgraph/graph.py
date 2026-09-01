from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from cashgraph.extract import extract_cashtags
from cashgraph.models import Edge, Extracted, NodeStats, Post
from cashgraph.universe import is_illiquid, is_mega, load_universe


def annotate(posts: list[Post]) -> list[Extracted]:
    out: list[Extracted] = []
    for p in posts:
        tags = extract_cashtags(p.text)
        if tags:
            out.append(Extracted(post=p, cashtags=tags))
    return out


def build_nodes(items: list[Extracted], universe=None) -> list[NodeStats]:
    universe = universe or load_universe()
    mentions: dict[str, int] = defaultdict(int)
    authors: dict[str, set[str]] = defaultdict(set)
    for it in items:
        for t in it.cashtags:
            mentions[t] += 1
            authors[t].add(it.post.author_id)
    nodes = []
    for tag, n in mentions.items():
        nodes.append(
            NodeStats(
                cashtag=tag,
                mentions=n,
                unique_authors=len(authors[tag]),
                mega=is_mega(tag, universe),
                illiquid=is_illiquid(tag, universe),
            )
        )
    nodes.sort(key=lambda x: (x.unique_authors, x.mentions), reverse=True)
    return nodes


def build_edges(items: list[Extracted], min_weight: float = 1.0) -> list[Edge]:
    pair_posts: dict[tuple[str, str], int] = defaultdict(int)
    pair_authors: dict[tuple[str, str], set[str]] = defaultdict(set)
    for it in items:
        tags = sorted(set(it.cashtags))
        if len(tags) < 2:
            continue
        for a, b in combinations(tags, 2):
            key = (a, b)
            pair_posts[key] += 1
            pair_authors[key].add(it.post.author_id)
    edges: list[Edge] = []
    for (a, b), posts in pair_posts.items():
        authors = len(pair_authors[(a, b)])
        weight = authors + 0.25 * posts
        if weight >= min_weight:
            edges.append(
                Edge(
                    source=a,
                    target=b,
                    weight=round(weight, 3),
                    unique_authors=authors,
                    posts=posts,
                )
            )
    edges.sort(key=lambda e: e.weight, reverse=True)
    return edges
