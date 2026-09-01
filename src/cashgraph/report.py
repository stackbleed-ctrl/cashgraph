from __future__ import annotations

import html
from pathlib import Path

from cashgraph.models import Snapshot

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>cashgraph</title>
<style>
  :root { color-scheme: dark; }
  body { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
         background:#0b0d10; color:#e8edf2; margin:0; padding:24px; }
  h1 { font-size:20px; letter-spacing:.08em; }
  h2 { font-size:15px; margin-top:28px; }
  .muted { color:#8b98a5; font-size:12px; }
  .warn { color:#f3c14e; }
  table { border-collapse:collapse; width:100%; margin:16px 0 32px; font-size:13px; }
  th,td { text-align:left; padding:6px 8px; border-bottom:1px solid #1c242c; vertical-align:top; }
  th { color:#8b98a5; font-weight:500; }
  .mega { color:#6ee7b7; }
  .illiquid { color:#f87171; }
  .tag { color:#7dd3fc; }
  .farm { color:#fb923c; }
</style>
</head>
<body>
<h1>$GRAPH</h1>
<p class="muted">generated __GENERATED__ · source __SOURCE__ · window __WINDOW__h · attention topology, not a price forecast</p>
__WARNINGS__
<h2>nodes</h2>
<table>
<tr><th>cashtag</th><th>mentions</th><th>unique</th><th>first-timers</th><th>ft share</th><th>Δ vs ~7d/7</th><th>flags</th></tr>
__NODES__
</table>
<h2>co-occurrence</h2>
<table>
<tr><th>source</th><th>target</th><th>weight</th><th>authors</th><th>posts</th></tr>
__EDGES__
</table>
<h2>piggyback radar</h2>
<table>
<tr><th>host</th><th>parasite</th><th>score</th><th>authors</th><th>reason</th></tr>
__PIGGY__
</table>
<h2>farm clusters</h2>
<table>
<tr><th>kind</th><th>score</th><th>authors</th><th>posts</th><th>handles</th><th>template / reason</th></tr>
__FARMS__
</table>
<h2>earliest non-reply origins</h2>
<table>
<tr><th>cashtag</th><th>when</th><th>account</th><th>likes</th><th>text</th></tr>
__ORIGINS__
</table>
</body></html>
"""


def write_report(snap: Snapshot, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "report.json"
    html_path = out_dir / "index.html"
    json_path.write_text(snap.model_dump_json(indent=2))

    warns = "".join(f'<p class="warn">warning: {html.escape(w)}</p>' for w in snap.warnings)
    nodes = "\n".join(
        "<tr>"
        f"<td class='tag'>${html.escape(n.cashtag)}</td>"
        f"<td>{n.mentions}</td><td>{n.unique_authors}</td>"
        f"<td>{n.first_timers}</td><td>{n.first_timer_share:.2f}</td>"
        f"<td>{n.unique_delta:+.1f}</td>"
        f"<td>{'mega ' if n.mega else ''}{'illiquid' if n.illiquid else ''}</td>"
        "</tr>"
        for n in snap.nodes
    ) or "<tr><td colspan=7>none</td></tr>"
    edges = "\n".join(
        f"<tr><td>${html.escape(e.source)}</td><td>${html.escape(e.target)}</td><td>{e.weight}</td>"
        f"<td>{e.unique_authors}</td><td>{e.posts}</td></tr>"
        for e in snap.edges[:80]
    ) or "<tr><td colspan=5>none</td></tr>"
    piggy = "\n".join(
        f"<tr><td class='mega'>${html.escape(p.host)}</td><td class='illiquid'>${html.escape(p.parasite)}</td>"
        f"<td>{p.score}</td><td>{p.unique_authors}</td><td>{html.escape(p.reason)}</td></tr>"
        for p in snap.piggybacks
    ) or "<tr><td colspan=5>none this window</td></tr>"
    farms = "\n".join(
        "<tr>"
        f"<td class='farm'>{html.escape(f.kind)}</td>"
        f"<td>{f.score}</td><td>{f.unique_authors}</td><td>{f.posts}</td>"
        f"<td>{html.escape(', '.join('@'+h for h in f.handles[:8]))}</td>"
        f"<td>{html.escape(f.template)} — {html.escape(f.reason)}</td>"
        "</tr>"
        for f in snap.farms
    ) or "<tr><td colspan=6>none this window</td></tr>"
    origins = "\n".join(
        f"<tr><td>${html.escape(o.cashtag)}</td><td>{html.escape(o.created_at.isoformat())}</td>"
        f"<td>@{html.escape(o.author_handle)}</td><td>{o.likes}</td><td>{html.escape(o.text)}</td></tr>"
        for o in snap.origins[:40]
    ) or "<tr><td colspan=5>none</td></tr>"

    page = (
        TEMPLATE.replace("__GENERATED__", html.escape(snap.generated_at.isoformat()))
        .replace("__SOURCE__", html.escape(snap.source))
        .replace("__WINDOW__", str(snap.window_hours))
        .replace("__WARNINGS__", warns)
        .replace("__NODES__", nodes)
        .replace("__EDGES__", edges)
        .replace("__PIGGY__", piggy)
        .replace("__FARMS__", farms)
        .replace("__ORIGINS__", origins)
    )
    html_path.write_text(page)
    return json_path, html_path
