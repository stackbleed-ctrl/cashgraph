# Cashgraph

Cashtag attention topology for X.

Not a sentiment dashboard. Not a price predictor.

`$GRAPH` v0.2 ships **three detectors plus a publish path** on one snapshot:

1. **Co-occurrence graph** — which cashtags travel together
2. **Piggyback radar** — illiquid / unknown tickers hitchhiking on mega cashtags
3. **Farm clusters** — copy-paste templates across accounts + single-account burst cadence
4. **First-timer tracker** — authors never before seen on that cashtag
5. **Origins** — earliest non-reply posts in the current batch
6. **GitHub Pages** — fixture report published from Actions
7. **Official X API adapter** — optional, fails closed without `X_BEARER_TOKEN`

## What this is not

- Not investment advice
- Not a claim that mention volume forecasts price
- Not a scraper. Unofficial X collection will get you banned and is not in this repo

## Quick start

```bash
git clone https://github.com/stackbleed-ctrl/cashgraph.git
cd cashgraph
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
cashgraph --source fixture --out data/out
```

Open `data/out/index.html`.

Second run against the same `--store data/state.sqlite` is when first-timer counts stop being “everyone is new.”

## GitHub Pages

For the repository owner:

1. Repo → Settings → Pages → Source: **GitHub Actions**
2. The `pages` workflow runs tests, generates `public/index.html` from **fixtures**, deploys

Pages stays on fixtures by default. Publishing live X posts from CI means storing a bearer token in GitHub and reprinting other people’s posts on a public site. Do that only if you accept both costs.

## Official X search

```bash
cp .env.example .env
# put the bearer token in .env, then:
export X_BEARER_TOKEN=...
pip install -e ".[dev,xapi]"
cashgraph --source xapi --tickers NVDA,TSLA,AAPL,BTC --min-faves 5 --out data/out
```

Tunables live in `data/xapi.json` (`query_suffix`, `min_faves`, pages, max results). Missing token → hard fail. 401/403/429 → hard fail with a readable reason.

Recent search is a paid X product. If your project does not include it, the adapter is dead code and that is fine.

## Repo layout

```
src/cashgraph/     extract, graph, piggyback, farms, store, xapi adapter
data/universe.json mega vs illiquid labels
data/fixture_posts.json  research posts + a synthetic raid
data/xapi.json     official search defaults
.github/workflows  pytest + Pages
```

## Attack surface / honesty

- First-timer % is meaningless until the sqlite store has history
- Template farms are detected by skeleton text, not by “AI vibes.” Aged unique accounts posting original text will slip through
- Burst detection is per-author time clustering, not a follow-graph
- Unknown tickers are treated as potential parasites — a prior, not proof of fraud
- `$SOL` is still a string node; asset-id split is not in this version
- Calibration / hit-rate scoring is still not in this slice
