from pathlib import Path

from cashgraph.collectors import FixtureCollector
from cashgraph.extract import extract_cashtags
from cashgraph.pipeline import run_pipeline
from cashgraph.report import write_report


def test_fixture_pipeline_finds_piggybacks(tmp_path: Path):
    snap = run_pipeline(FixtureCollector(), tmp_path / "state.sqlite", window_hours=6)
    hosts = {(p.host, p.parasite) for p in snap.piggybacks}
    assert ("NVDA", "PUMP") in hosts
    assert ("AAPL", "XYZQ") in hosts
    assert any(n.cashtag == "NVDA" for n in snap.nodes)
    assert any(e.source == "NVDA" and e.target == "TSM" for e in snap.edges) or any(
        e.source == "TSM" and e.target == "NVDA" for e in snap.edges
    )
    assert snap.source == "fixture"
    assert any(f.kind == "template" for f in snap.farms)
    assert any(f.kind == "burst" for f in snap.farms)
    assert snap.summary.posts == len(snap.events)
    assert snap.summary.coordinated_posts > 0
    assert any(event.coordinated for event in snap.events)


def test_campaign_radar_report_is_interactive(tmp_path: Path):
    snap = run_pipeline(FixtureCollector(), tmp_path / "state.sqlite", window_hours=6)
    _, html_path = write_report(snap, tmp_path / "report")
    page = html_path.read_text()
    assert "campaign replay" in page
    assert "exclude coordinated posts" in page
    assert 'id="cashgraph-data"' in page
    assert '"coordinated": true' in page


def test_reply_not_used_as_only_origin_filter():
    # origin helper skips replies; NVDA still has non-reply origins
    from cashgraph.collectors import FixtureCollector
    from cashgraph.graph import annotate
    from cashgraph.origins import earliest_origins

    items = annotate(FixtureCollector().fetch())
    origins = earliest_origins(items)
    nvda = [o for o in origins if o.cashtag == "NVDA"]
    assert nvda
    assert nvda[0].author_handle == "chip_notes"


def test_dollar_amount_not_cashtag():
    assert extract_cashtags("costs $1000 today") == []
