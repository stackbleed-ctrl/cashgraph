from datetime import datetime, timezone

from cashgraph.farms import detect_farms, normalize_template
from cashgraph.graph import annotate
from cashgraph.models import Post


def _p(i: str, author: str, text: str, minute: int) -> Post:
    return Post(
        id=i,
        author_id=author,
        author_handle=author,
        text=text,
        created_at=datetime(2026, 9, 1, 12, minute, tzinfo=timezone.utc),
    )


def test_normalize_collapses_cashtags_urls():
    a = normalize_template("$NVDA $PUMP moon setup join my room")
    b = normalize_template("https://x.com/x $TSLA $XYZQ moon setup join my room")
    assert a == b
    assert "$ticker" in a


def test_template_farm_needs_three_authors():
    posts = [
        _p("1", "a", "$NVDA moon setup join my room", 1),
        _p("2", "b", "$TSLA moon setup join my room", 2),
        _p("3", "c", "$AAPL moon setup join my room", 3),
        _p("4", "d", "unique research note on $NVDA supply", 4),
    ]
    farms = detect_farms(annotate(posts))
    kinds = {f.kind for f in farms}
    assert "template" in kinds
    tmpl = next(f for f in farms if f.kind == "template")
    assert tmpl.unique_authors == 3


def test_burst_farm_same_author():
    posts = [
        _p("1", "spray", "$NVDA add", 1),
        _p("2", "spray", "$TSLA add", 2),
        _p("3", "spray", "$AAPL add", 3),
    ]
    farms = detect_farms(annotate(posts))
    assert any(f.kind == "burst" and f.posts == 3 for f in farms)
