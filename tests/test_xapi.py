import json
from datetime import datetime, timezone

from cashgraph.collectors import XApiCollector
from cashgraph.models import Post


class FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


class FakeClient:
    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = 0

    def get(self, url, headers=None, params=None):
        i = min(self.calls, len(self.pages) - 1)
        self.calls += 1
        return FakeResp(self.pages[i])


def test_xapi_maps_payload(monkeypatch, tmp_path):
    cfg = tmp_path / "xapi.json"
    cfg.write_text(json.dumps({"query_suffix": "-is:retweet", "pages": 1, "max_results_per_ticker": 10}))
    page = {
        "data": [
            {
                "id": "99",
                "author_id": "u1",
                "text": "hello $NVDA",
                "created_at": "2026-09-01T12:00:00.000Z",
                "public_metrics": {"like_count": 4, "retweet_count": 1, "reply_count": 0},
            }
        ],
        "includes": {
            "users": [
                {
                    "id": "u1",
                    "username": "chip",
                    "public_metrics": {"followers_count": 12},
                }
            ]
        },
        "meta": {},
    }
    collector = XApiCollector(["NVDA"], token="fake", config_path=cfg)

    def fake_search(self, client, headers, tag, seen):
        return [
            Post(
                id="99",
                author_id="u1",
                author_handle="chip",
                text="hello $NVDA",
                created_at=datetime(2026, 9, 1, 12, tzinfo=timezone.utc),
                likes=4,
            )
        ]

    monkeypatch.setattr(XApiCollector, "_search_tag", fake_search)
    posts = collector.fetch()
    assert posts[0].author_handle == "chip"
    assert posts[0].likes == 4


def test_xapi_refuses_missing_token():
    c = XApiCollector(["NVDA"], token="")
    try:
        c.fetch()
        assert False, "should have failed closed"
    except RuntimeError as e:
        assert "X_BEARER_TOKEN" in str(e)
