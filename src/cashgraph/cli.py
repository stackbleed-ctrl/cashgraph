from __future__ import annotations

import argparse
from pathlib import Path

from cashgraph.collectors import FixtureCollector, XApiCollector
from cashgraph.pipeline import run_pipeline
from cashgraph.report import write_report
from cashgraph.universe import load_universe


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cashgraph", description="Cashtag attention topology")
    p.add_argument("--source", choices=["fixture", "xapi"], default="fixture")
    p.add_argument("--out", type=Path, default=Path("data/out"))
    p.add_argument("--store", type=Path, default=Path("data/state.sqlite"))
    p.add_argument("--window-hours", type=int, default=6)
    p.add_argument(
        "--tickers",
        default="",
        help="comma-separated tickers for xapi source; default = mega names in universe",
    )
    p.add_argument("--min-faves", type=int, default=0)
    p.add_argument("--max-results", type=int, default=50)
    args = p.parse_args(argv)

    if args.source == "fixture":
        collector = FixtureCollector()
    else:
        uni = load_universe()
        if args.tickers:
            tags = [t.strip().lstrip("$").upper() for t in args.tickers.split(",") if t.strip()]
        else:
            tags = [k for k, a in uni.items() if a.mega][:12]
        collector = XApiCollector(
            tags,
            max_results=args.max_results,
            min_faves=args.min_faves,
        )

    snap = run_pipeline(collector, args.store, args.window_hours)
    json_path, html_path = write_report(snap, args.out)
    print(
        f"source={snap.source} nodes={len(snap.nodes)} edges={len(snap.edges)} "
        f"piggybacks={len(snap.piggybacks)} farms={len(snap.farms)}"
    )
    print(f"wrote {json_path}")
    print(f"wrote {html_path}")
    for w in snap.warnings:
        print(f"WARN: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
