from __future__ import annotations

import html
import json
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
         background:#0b0d10; color:#e8edf2; margin:0; padding:24px; overflow-x:hidden; }
  h1 { font-size:20px; letter-spacing:.08em; }
  h2 { font-size:15px; margin-top:28px; }
  .muted { color:#8b98a5; font-size:12px; }
  .warn { color:#f3c14e; }
  table { border-collapse:collapse; width:100%; margin:16px 0 32px; font-size:13px; display:block; overflow-x:auto; }
  th,td { text-align:left; padding:6px 8px; border-bottom:1px solid #1c242c; vertical-align:top; }
  th { color:#8b98a5; font-weight:500; }
  .mega { color:#6ee7b7; }
  .illiquid { color:#f87171; }
  .tag { color:#7dd3fc; }
  .farm { color:#fb923c; }
  * { box-sizing:border-box; }
  body { background:radial-gradient(circle at 80% -10%,#15324a 0,transparent 34%),#070a0d; }
  .shell { max-width:1200px; margin:auto; }
  .eyebrow { color:#7dd3fc; letter-spacing:.18em; text-transform:uppercase; font-size:11px; }
  .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(145px,1fr)); gap:10px; margin:24px 0; }
  .card,.panel { background:#0d1319dd; border:1px solid #1c2b36; border-radius:14px; box-shadow:0 16px 40px #0005; }
  .card { padding:16px; }
  .card b { display:block; font-size:26px; color:#fff; margin-top:7px; }
  .panel { padding:16px; margin:14px 0; overflow:hidden; min-width:0; }
  .controls { display:flex; flex-wrap:wrap; align-items:center; gap:14px; margin-bottom:12px; }
  .controls button { background:#102b3b; color:#7dd3fc; border:1px solid #24506a; border-radius:8px; padding:8px 12px; }
  input[type=range] { width:100%; accent-color:#38bdf8; }
  #graph { width:100%; min-height:420px; display:block; }
  .edge { stroke:#2c4d60; stroke-opacity:.65; }
  .node { stroke:#071018; stroke-width:3; cursor:pointer; }
  .node.selected { stroke:#fff; stroke-width:5; filter:drop-shadow(0 0 8px #7dd3fc); }
  .node-label { fill:#dbeafe; font-size:11px; pointer-events:none; text-anchor:middle; }
  .event { border-left:3px solid #334155; padding:8px 10px; margin:7px 0; background:#0a0f14; }
  .event.coordinated { border-color:#fb923c; }
  .pill { display:inline-block; border:1px solid #334155; border-radius:99px; padding:2px 7px; margin-right:5px; font-size:10px; }
  .split { display:grid; grid-template-columns:1.45fr 1fr; gap:14px; }
  @media(max-width:800px){
    body{padding:18px 14px} .split{grid-template-columns:1fr} .panel{padding:12px}
    #graph{min-height:480px} .node-label{font-size:12px} h1{font-size:28px}
  }
</style>
</head>
<body>
<main class="shell">
<div class="eyebrow">campaign intelligence · evidence first</div>
<h1>$GRAPH</h1>
<p class="muted">generated __GENERATED__ · source __SOURCE__ · window __WINDOW__h · attention topology, not a price forecast</p>
__WARNINGS__
<section class="cards">
<div class="card"><span class="muted">posts</span><b id="m-posts">0</b></div>
<div class="card"><span class="muted">authors</span><b id="m-authors">0</b></div>
<div class="card"><span class="muted">campaign signals</span><b id="m-campaigns">0</b></div>
<div class="card"><span class="muted">coordinated share</span><b id="m-share">0%</b></div>
</section>
<div class="split">
<section class="panel"><div class="controls"><strong>attention graph</strong><label><input id="organic" type="checkbox"> exclude coordinated posts</label></div><svg id="graph" viewBox="0 0 760 440"></svg><p id="graph-note" class="muted">Select a node to inspect its connections.</p></section>
<section class="panel"><div class="controls"><strong>campaign replay</strong><button id="play">▶ play</button></div><input id="timeline" type="range" min="0" value="0" step="1"><p id="clock" class="muted"></p><div id="events"></div></section>
</div>
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
<script id="cashgraph-data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('cashgraph-data').textContent),$=id=>document.getElementById(id);
$('m-posts').textContent=D.summary.posts;$('m-authors').textContent=D.summary.authors;$('m-campaigns').textContent=D.summary.campaigns;$('m-share').textContent=Math.round(D.summary.coordinated_share*100)+'%';
const slider=$('timeline');slider.max=Math.max(0,D.events.length-1);slider.value=slider.max;let timer=null;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function visible(){return D.events.slice(0,Number(slider.value)+1).filter(e=>!$('organic').checked||!e.coordinated)}
function graph(events){const counts={},pairs={},mobile=innerWidth<700,W=mobile?380:760,H=mobile?500:440;events.forEach(e=>{e.cashtags.forEach(t=>counts[t]=(counts[t]||0)+1);for(let i=0;i<e.cashtags.length;i++)for(let j=i+1;j<e.cashtags.length;j++){const k=[e.cashtags[i],e.cashtags[j]].sort().join('|');pairs[k]=(pairs[k]||0)+1}});const names=Object.keys(counts).sort((a,b)=>counts[b]-counts[a]).slice(0,18),pos={},cx=W/2,cy=H/2,rad=mobile?145:155;$('graph').setAttribute('viewBox',`0 0 ${W} ${H}`);names.forEach((n,i)=>{const a=2*Math.PI*i/names.length-Math.PI/2;pos[n]=[cx+Math.cos(a)*rad,cy+Math.sin(a)*rad]});let out='';Object.entries(pairs).forEach(([k,w])=>{const[a,b]=k.split('|');if(pos[a]&&pos[b])out+=`<line class="edge" x1="${pos[a][0]}" y1="${pos[a][1]}" x2="${pos[b][0]}" y2="${pos[b][1]}" stroke-width="${Math.min(8,1+w)}"/>`});names.forEach(n=>{const[x,y]=pos[n],meta=D.nodes.find(v=>v.cashtag===n)||{},color=meta.illiquid?'#f87171':meta.mega?'#34d399':'#38bdf8',r=mobile?12+Math.min(18,counts[n]*2):10+Math.min(20,counts[n]*2);out+=`<circle class="node" data-name="${esc(n)}" cx="${x}" cy="${y}" r="${r}" data-r="${r}" fill="${color}"/><text class="node-label" x="${x}" y="${y+r+18}">$${esc(n)}</text>`});$('graph').innerHTML=out||`<text x="${cx}" y="${cy}" text-anchor="middle" fill="#8b98a5">No activity</text>`;document.querySelectorAll('.node').forEach(n=>n.onclick=()=>{document.querySelectorAll('.node').forEach(v=>{v.classList.remove('selected');v.setAttribute('r',v.dataset.r)});n.classList.add('selected');n.setAttribute('r',Number(n.dataset.r)+6);const name=n.dataset.name,links=Object.entries(pairs).filter(([k])=>k.split('|').includes(name)).sort((a,b)=>b[1]-a[1]).slice(0,5);$('graph-note').textContent=`$${name}: ${counts[name]} visible mentions · `+(links.map(([k,w])=>'$'+k.split('|').find(x=>x!==name)+' ×'+w).join(' · ')||'no co-occurrences')})}
function render(){const rows=visible(),latest=D.events[Number(slider.value)];$('clock').textContent=latest?new Date(latest.created_at).toLocaleString():'no activity';$('events').innerHTML=rows.slice(-7).reverse().map(e=>`<div class="event ${e.coordinated?'coordinated':''}"><span class="pill">@${esc(e.author_handle)}</span>${e.cashtags.map(t=>`<span class="pill">$${esc(t)}</span>`).join('')}<div>${esc(e.text)}</div></div>`).join('')||'<p class="muted">No events in this view.</p>';graph(rows)}
slider.oninput=render;$('organic').onchange=render;$('play').onclick=()=>{if(timer){clearInterval(timer);timer=null;$('play').textContent='▶ play';return}slider.value=0;$('play').textContent='■ stop';timer=setInterval(()=>{if(Number(slider.value)>=Number(slider.max)){clearInterval(timer);timer=null;$('play').textContent='▶ play';return}slider.value=Number(slider.value)+1;render()},650)};render();
</script>
</main>
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
        .replace("__DATA__", json.dumps(snap.model_dump(mode="json")).replace("</", "<\\/"))
    )
    html_path.write_text(page)
    return json_path, html_path
