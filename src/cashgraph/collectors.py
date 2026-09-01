from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Protocol

from cashgraph.models import Post

FIXTURE = Path(__file__).resolve().parents[2] / "data" / "fixture_posts.json"
XAPI_DEFAULTS = Path(__file__).resolve().parents[2] / "data" / "xapi.json"
API_BASE = os.environ.get("X_API_BASE", "https://api.twitter.com").rstrip("/")


class Collector(Protocol):
    source_name: str

    def fetch(self) -> list[Post]: ...


def _parse_post_row(row: dict) -> Post:
    row = dict(row)
    if isinstance(row.get("created_at"), str):
        row["created_at"] = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
    if row.get("author_created_at"):
        row["author_created_at"] = datetime.fromisoformat(
            str(row["author_created_at"]).replace("Z", "+00:00")
        )
    return Post(**row)


class FixtureCollector:
    source_name = "fixture"

    def __init__(self, path: Path | None = None):
        self.path = path or FIXTURE

    def fetch(self) -> list[Post]:
        raw = json.loads(self.path.read_text())
        return [_parse_post_row(row) for row in raw]


class XApiCollector:
    """Official X API v2 recent search only. Requires X_BEARER_TOKEN.

    Fails closed. Does not scrape. Pagination is capped to keep the bill finite.
    """

    source_name = "xapi"

    def __init__(
        self,
        cashtags: list[str],
        max_results: int = 50,
        min_faves: int = 0,
        pages: int = 2,
        token: str | None = None,
        config_path: Path | None = None,
    ):
        cfg = {}
        path = config_path or XAPI_DEFAULTS
        if path.exists():
            cfg = json.loads(path.read_text())
        self.cashtags = [t.lstrip("$").upper() for t in cashtags]
        self.max_results = int(cfg.get("max_results_per_ticker", max_results))
        self.min_faves = int(cfg.get("min_faves", min_faves))
        self.pages = int(cfg.get("pages", pages))
        self.query_suffix = cfg.get("query_suffix", "-is:retweet lang:en")
        self.token = token if token is not None else os.environ.get("X_BEARER_TOKEN", "")

    def fetch(self) -> list[Post]:
        if not self.token:
            raise RuntimeError(
                "X_BEARER_TOKEN not set. Use --source fixture or export a bearer token."
            )
        try:
            import httpx
        except ImportError as e:
            raise RuntimeError("Install extra: pip install 'cashgraph[xapi]'") from e

        posts: list[Post] = []
        seen: set[str] = set()
        headers = {"Authorization": f"Bearer {self.token}"}
        with httpx.Client(timeout=30.0) as client:
            for tag in self.cashtags:
                posts.extend(self._search_tag(client, headers, tag, seen))
        return posts

    def _search_tag(self, client, headers: dict, tag: str, seen: set[str]) -> list[Post]:
        parts = [f"${tag}", self.query_suffix]
        if self.min_faves > 0:
            parts.append(f"min_faves:{self.min_faves}")
        query = " ".join(p for p in parts if p)
        params = {
            "query": query,
            "max_results": str(min(max(self.max_results, 10), 100)),
            "tweet.fields": "created_at,public_metrics,author_id,in_reply_to_user_id",
            "user.fields": "username,created_at,public_metrics",
            "expansions": "author_id",
        }
        url = f"{API_BASE}/2/tweets/search/recent"
        out: list[Post] = []
        for _ in range(max(self.pages, 1)):
            r = client.get(url, headers=headers, params=params)
            if r.status_code == 401:
                raise RuntimeError("X API 401 — bearer token rejected")
            if r.status_code == 403:
                raise RuntimeError("X API 403 — product access missing for recent search")
            if r.status_code == 429:
                raise RuntimeError("X API 429 — rate limited. back off before retrying")
            r.raise_for_status()
            data = r.json()
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            for t in data.get("data", []):
                if t["id"] in seen:
                    continue
                seen.add(t["id"])
                u = users.get(t.get("author_id"), {})
                metrics = t.get("public_metrics", {})
                created = t.get("created_at", "1970-01-01T00:00:00Z")
                out.append(
                    Post(
                        id=t["id"],
                        author_id=t.get("author_id", ""),
                        author_handle=u.get("username", t.get("author_id", "")),
                        text=t.get("text", ""),
                        created_at=datetime.fromisoformat(created.replace("Z", "+00:00")),
                        likes=metrics.get("like_count", 0),
                        reposts=metrics.get("retweet_count", 0),
                        replies=metrics.get("reply_count", 0),
                        is_reply=bool(t.get("in_reply_to_user_id")),
                        followers=u.get("public_metrics", {}).get("followers_count", 0),
                    )
                )
            nxt = data.get("meta", {}).get("next_token")
            if not nxt:
                break
            params = dict(params)
            params["next_token"] = nxt
        return out
