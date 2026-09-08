# Real-time Airfare Price Index (APIx) — Internal Round Prototype

This is the "safe demo core" of the SIH problem statement: a working
scrape → clean → index pipeline that runs end-to-end without depending on
live websites (which can break mid-demo due to anti-bot measures).

## What's here

| File | Purpose |
|---|---|
| `mock_data_generator.py` | Simulates raw scraped airfare quotes (6 routes × 5 carriers × 5 advance-purchase windows × 45 days), including realistic noise: sold-out flights, missing fields, outliers. |
| `data_cleaning.py` | Drops sold-outs, fixes/recomputes missing base_fare/taxes/total_fare, removes statistical outliers per route+window (IQR method), de-duplicates. |
| `index_calculator.py` | Computes the daily APIx using a Laspeyres-style weighted price-relative formula (same family as real CPI methodology), plus weekly/monthly rollups and a per-route sub-index. |
| `main.py` | Runs all three stages + generates a trend chart. **Run this for the full demo.** |

## How to run

```bash
pip install pandas numpy matplotlib
python3 main.py
```

Outputs generated:
- `raw_airfare_quotes.csv` — simulated raw scrape
- `clean_airfare_quotes.csv` — cleaned data
- `apix_daily.csv` / `apix_weekly.csv` / `apix_monthly.csv` — the index at each frequency
- `apix_route_breakdown.csv` — per-route sub-index (feeds the heatmap in the dashboard)
- `apix_trend_chart.png` — visual trend

## Index formula

```
APIx_t = 100 * Σ ( weight_route × (price_route,t / price_route,base) )
```

- `price_route,t` = average total fare for that route on day t (across carriers + advance windows)
- `price_route,base` = average fare in the base period (first 7 days)
- `weight_route` = route's share of the basket — currently illustrative, **swap in real DGCA passenger-traffic weights before the final round**

## What's real vs. simulated right now

- ✅ Real: cleaning logic, index math, weighting method, CSV schema, chart
- 🔶 Simulated: the "scraper" — `mock_data_generator.py` stands in for Playwright/Scrapy hitting live sites

## Running it as one working website (local)

```bash
pip install pandas numpy matplotlib fastapi uvicorn
python3 main.py                 # generates all the CSVs
python3 export_static_data.py   # converts CSVs -> data/*.json (dashboard reads these)
uvicorn api:app --reload        # starts the website
```

Open **http://127.0.0.1:8000/**. `api.py` serves the dashboard HTML at `/`
and the `data/*.json` files at `/data/*` — this is the exact same file
GitHub Pages will serve statically, just running through a local server
here. It also exposes `/apix/*` as a separate JSON API (for NSO/RBI-style
programmatic consumers, per the problem statement) — the dashboard itself
doesn't use these, `/data/*.json` is what it fetches.

## Deploying to GitHub Pages (no server needed)

GitHub Pages only serves static files — it can't run `api.py`. So instead,
`export_static_data.py` bakes the pipeline's output into plain JSON files
that the dashboard fetches directly. This version **was verified working**
end-to-end locally (served over `python3 -m http.server`, confirmed the
dashboard loads and renders from the JSON files).

```bash
python3 main.py                 # generate the CSVs
python3 export_static_data.py   # convert CSVs -> data/*.json
```

This creates a `data/` folder with `daily.json`, `weekly.json`,
`monthly.json`, `heatmap.json`, `elasticity.json`.

**Important:** don't just double-click `apix_dashboard.html` to test this —
browsers block `fetch()` of local files opened via `file://`. Test locally
with a tiny server first:
```bash
python3 -m http.server 8000
```
then visit `http://localhost:8000/apix_dashboard.html`.

**To publish on GitHub Pages:**
1. Create a new GitHub repo, push this folder to it (at minimum you need
   `apix_dashboard.html` and the `data/` folder — the `.py` files aren't
   needed for the site itself, only to regenerate `data/` later)
2. On GitHub: repo **Settings → Pages → Source** → select your branch
   (usually `main`) and root folder → Save
3. GitHub gives you a URL like `https://<username>.github.io/<repo-name>/`
4. Since `apix_dashboard.html` isn't named `index.html`, visit
   `https://<username>.github.io/<repo-name>/apix_dashboard.html`
   directly, or rename the file to `index.html` before pushing so it
   loads at the root URL

**Note on "live" data:** this version is a snapshot, not truly real-time —
GitHub Pages can't run your Python pipeline on a schedule. To refresh it,
re-run the two commands above and push the updated `data/` folder. For a
finals-round production version, you'd run the pipeline on a schedule
(cron/GitHub Actions) and have that push updated JSON automatically.

## Dashboard

`apix_dashboard.html` — self-contained frontend, fetches from the API's
`/apix/*` endpoints. No build step, no npm, works in any browser.
`apix_dashboard.jsx` — an equivalent React version, only needed if you
later fold this into a larger React app.

## Real scraper (`real_scraper.py`) — status: UNTESTED, needs your work

This is a Playwright template, not a finished scraper. It was written
without live internet access, so:
- CSS selectors are placeholders marked `ADJUST` — you must inspect the
  real site with browser dev tools and fill these in yourself
- It checks `robots.txt` at runtime rather than assuming what it says
- It intentionally has **no CAPTCHA-solving or IP-rotation code** — that
  crosses from "automating a browsing session" into "defeating a site's
  anti-bot protections," which is a different and legally greyer thing.
  If you hit blocks: scrape fewer routes, lower frequency, or look into
  official partner/affiliate APIs (several OTAs offer these) for a real
  production version.

Run with: `pip install playwright && playwright install chromium`, then
fix the `ADJUST` selectors before running.

## Next steps (not built yet)

1. **Finish the real scraper** — fill in real selectors (see above)
2. **API endpoint** — thin FastAPI wrapper exposing `apix_daily.csv` as JSON
3. **Real DGCA weights** — replace the illustrative `ROUTE_WEIGHTS` in `index_calculator.py`
4. **Backtest** — once real data exists, compare `apix_monthly.csv` against publicly available DGCA monthly average fares
