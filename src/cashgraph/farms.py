from __future__ import annotations

import re
from collections import defaultdict
from datetime import timedelta

from cashgraph.models import Extracted, FarmCluster

_URL = re.compile(r"https?://\S+", re.I)
_MENTION = re.compile(r"@\w+")
_CASHTAG = re.compile(r"\$[A-Za-z][A-Za-z0-9.-]*")
_NON_ALNUM = re.compile(r"[^a-z0-9\s$]+")
_SPACE = re.compile(r"\s+")

_INVITE = (
    "join my",
    "join the room",
    "discord.gg",
    "dm me",
    "signal group",
    "free calls",
    "last chance",
)


def normalize_template(text: str) -> str:
    """Strip identity noise so copy-paste raids collapse to one skeleton."""
    t = text.lower()
    t = _URL.sub(" ", t)
    t = _MENTION.sub(" ", t)
    t = _CASHTAG.sub(" $ticker ", t)
    t = _NON_ALNUM.sub(" ", t)
    t = _SPACE.sub(" ", t).strip()
    return t


def detect_farms(
    items: list[Extracted],
    min_template_authors: int = 3,
    burst_posts: int = 3,
    burst_minutes: int = 10,
) -> list[FarmCluster]:
    clusters: list[FarmCluster] = []
    clusters.extend(_template_clusters(items, min_template_authors))
    clusters.extend(_burst_clusters(items, burst_posts, burst_minutes))
    clusters.sort(key=lambda c: c.score, reverse=True)
    return clusters


def _template_clusters(items: list[Extracted], min_authors: int) -> list[FarmCluster]:
    buckets: dict[str, list[Extracted]] = defaultdict(list)
    for it in items:
        key = normalize_template(it.post.text)
        if len(key) < 12:
            continue
        buckets[key].append(it)

    out: list[FarmCluster] = []
    for tmpl, rows in buckets.items():
        authors = {r.post.author_id for r in rows}
        if len(authors) < min_authors:
            continue
        invite = any(tok in tmpl for tok in _INVITE)
        score = len(authors) * 2.0 + len(rows) * 0.4
        if invite:
            score += 3.0
        out.append(
            FarmCluster(
                kind="template",
                template=tmpl,
                score=round(score, 2),
                unique_authors=len(authors),
                posts=len(rows),
                handles=sorted({r.post.author_handle for r in rows}),
                post_ids=[r.post.id for r in rows],
                reason="same skeleton text across multiple accounts"
                + (" + invite/spam lexicon" if invite else ""),
            )
        )
    return out


def _burst_clusters(
    items: list[Extracted], burst_posts: int, burst_minutes: int
) -> list[FarmCluster]:
    by_author: dict[str, list[Extracted]] = defaultdict(list)
    for it in items:
        by_author[it.post.author_id].append(it)

    out: list[FarmCluster] = []
    window = timedelta(minutes=burst_minutes)
    for author_id, rows in by_author.items():
        rows = sorted(rows, key=lambda r: r.post.created_at)
        if len(rows) < burst_posts:
            continue
        i = 0
        while i < len(rows):
            j = i
            while j + 1 < len(rows) and rows[j + 1].post.created_at - rows[i].post.created_at <= window:
                j += 1
            chunk = rows[i : j + 1]
            if len(chunk) >= burst_posts:
                handle = chunk[0].post.author_handle
                out.append(
                    FarmCluster(
                        kind="burst",
                        template=f"@{handle} {len(chunk)} posts / {burst_minutes}m",
                        score=round(len(chunk) * 1.5, 2),
                        unique_authors=1,
                        posts=len(chunk),
                        handles=[handle],
                        post_ids=[r.post.id for r in chunk],
                        reason=f"single account fired {len(chunk)} cashtag posts inside {burst_minutes} minutes",
                    )
                )
                i = j + 1
            else:
                i += 1
    return out
