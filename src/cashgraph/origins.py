from __future__ import annotations

from cashgraph.models import Extracted, Origin


def earliest_origins(items: list[Extracted], per_tag: int = 3) -> list[Origin]:
    by_tag: dict[str, list[Extracted]] = {}
    for it in items:
        if it.post.is_reply:
            continue
        for tag in it.cashtags:
            by_tag.setdefault(tag, []).append(it)
    origins: list[Origin] = []
    for tag, rows in by_tag.items():
        rows.sort(key=lambda r: r.post.created_at)
        for it in rows[:per_tag]:
            origins.append(
                Origin(
                    cashtag=tag,
                    post_id=it.post.id,
                    author_handle=it.post.author_handle,
                    created_at=it.post.created_at,
                    likes=it.post.likes,
                    text=it.post.text[:240],
                )
            )
    origins.sort(key=lambda o: o.created_at)
    return origins
