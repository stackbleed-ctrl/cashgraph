from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from cashgraph.collectors import Collector
from cashgraph.farms import detect_farms
from cashgraph.graph import annotate, build_edges, build_nodes
from cashgraph.models import Snapshot
from cashgraph.origins import earliest_origins
from cashgraph.piggyback import detect_piggybacks
from cashgraph.store import AuthorStore, attach_first_timers
from cashgraph.universe import load_universe


def run_pipeline(
    collector: Collector,
    store_path: Path,
    window_hours: int = 6,
) -> Snapshot:
    posts = collector.fetch()
    items = annotate(posts)
    universe = load_universe()
    nodes = build_nodes(items, universe)
    edges = build_edges(items)
    piggy = detect_piggybacks(items, universe)
    farms = detect_farms(items)
    origins = earliest_origins(items)

    store = AuthorStore(store_path)
    first = store.apply(items)
    nodes = attach_first_timers(nodes, first, store, window_hours)
    store.close()

    warnings = []
    if not posts:
        warnings.append("collector returned zero posts")
    if all(n.first_timer_share == 1.0 for n in nodes if n.unique_authors):
        warnings.append(
            "every author looks like a first-timer — store was empty. "
            "run again over days before trusting unique_delta"
        )
    if farms:
        warnings.append(f"{len(farms)} farm cluster(s) — treat unique_author counts as inflated")

    return Snapshot(
        generated_at=datetime.now(timezone.utc),
        window_hours=window_hours,
        source=getattr(collector, "source_name", "unknown"),
        nodes=nodes,
        edges=edges,
        piggybacks=piggy,
        farms=farms,
        origins=origins,
        warnings=warnings,
    )
