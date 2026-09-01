from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cashgraph.models import Extracted, NodeStats

SCHEMA = """
CREATE TABLE IF NOT EXISTS sightings (
  cashtag TEXT NOT NULL,
  author_id TEXT NOT NULL,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  PRIMARY KEY (cashtag, author_id)
);
CREATE INDEX IF NOT EXISTS idx_sightings_tag ON sightings(cashtag);
"""


class AuthorStore:
    """Tracks which authors have been seen on a cashtag before (first-timers)."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def apply(self, items: list[Extracted], now: datetime | None = None) -> dict[str, int]:
        """Record sightings. Returns first-timer counts per cashtag for this batch."""
        now = now or datetime.now(timezone.utc)
        first: dict[str, int] = {}
        for it in items:
            ts = it.post.created_at.astimezone(timezone.utc).isoformat()
            for tag in it.cashtags:
                row = self.conn.execute(
                    "SELECT first_seen FROM sightings WHERE cashtag=? AND author_id=?",
                    (tag, it.post.author_id),
                ).fetchone()
                if row is None:
                    self.conn.execute(
                        "INSERT INTO sightings(cashtag, author_id, first_seen, last_seen) VALUES (?,?,?,?)",
                        (tag, it.post.author_id, ts, ts),
                    )
                    first[tag] = first.get(tag, 0) + 1
                else:
                    self.conn.execute(
                        "UPDATE sightings SET last_seen=? WHERE cashtag=? AND author_id=?",
                        (ts, tag, it.post.author_id),
                    )
        self.conn.commit()
        return first

    def unique_in_window(self, cashtag: str, hours: int, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        cutoff = (now - timedelta(hours=hours)).isoformat()
        row = self.conn.execute(
            "SELECT COUNT(*) FROM sightings WHERE cashtag=? AND last_seen>=?",
            (cashtag, cutoff),
        ).fetchone()
        return int(row[0]) if row else 0


def attach_first_timers(
    nodes: list[NodeStats],
    first_counts: dict[str, int],
    store: AuthorStore,
    window_hours: int,
    now: datetime | None = None,
) -> list[NodeStats]:
    now = now or datetime.now(timezone.utc)
    out = []
    for n in nodes:
        ft = first_counts.get(n.cashtag, 0)
        baseline = store.unique_in_window(n.cashtag, window_hours * 7, now) / 7.0
        share = ft / n.unique_authors if n.unique_authors else 0.0
        delta = n.unique_authors - baseline
        out.append(
            n.model_copy(
                update={
                    "first_timers": ft,
                    "first_timer_share": round(share, 3),
                    "baseline_unique": round(baseline, 2),
                    "unique_delta": round(delta, 2),
                }
            )
        )
    return out
