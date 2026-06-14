# Ekstraklasa 2025/26 Analytics

End-to-end analytics on the Polish top flight 2025/26 season. Multi-source scraping behind two anti-bot stacks, xG-based modelling, team-style clustering, season-long form trajectories, per-player percentile analysis and a multi-page Streamlit app on top of everything.

| Layer | Tech |
|---|---|
| Scraping | Playwright + Chrome DevTools Protocol |
| Cleaning | pandas |
| Analysis | Jupyter |
| App | Streamlit + Plotly |
| BI | Power BI |

## Streamlit app

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ekstraklasa-2025-26-analytics.streamlit.app/)

The main artifact. Five pages plus a rich home overview. Reads directly from `data/processed/`.

**streamlit_home_overview.png**

**streamlit_home_clusters_records.png**

| Page | What it shows |
|---|---|
| **Home / League overview** | Headline KPIs, xPts standings, Pts vs xPts scatter, position by matchweek bump chart, xPts breakdown heatmap, KMeans style clusters, records and extremes tabs. |
| **Club Profile** | Pick a club. Headline metrics, actual vs expected trajectory, rolling 5-match xG/xGA, team shot map, goal sources by situation, match log, top contributors and per-club records and extremes. |
| **Head-to-Head** | Pick any two clubs. Direct meetings table, style fingerprint radar, cumulative points, rolling xG comparison, shot maps side by side. |
| **Player Explorer** | Filter by team / role / minutes / age / market value. Pick a player and see their pizza, shot map and match-by-match performance trend. |
| **Player Compare** | Two modes (Outfield / GK). Side-by-side pizzas, shot maps and per-90 stat comparison. |
| **Scouting Tool** | Cosine similarity on the per-90 vector. Filter by MV cap, age window and same-team exclusion. Returns role-matched candidates only. |

**streamlit_club_profile.png**

**streamlit_player_explorer.png**

**streamlit_player_compare.png**

**streamlit_scouting_tool.png**

### Run locally

```powershell
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Notebooks

Three Jupyter notebooks. Each has a companion sub-README with the full chart gallery.

### 01 - Three Clubs Analysis

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1WkE71OOVvHdRSHehyfqPhypmKhN91K0A?usp=sharing)

Comparative analysis of Lech, Jaga and Legia on FBref counting stats. Season trajectory, form, splits, head-to-head, key players, goalkeeper rotation story. **Limited scope** - this notebook predates the Sofascore scrape and runs on counting stats only. Notebooks 02 and 03 are the xG-enabled versions.

**notebook_01_hero.png**

[Full sub-README](notebooks/01_three_clubs_analysis.md)

### 02 - Team Analytics

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1QopjjtC60sVqMAck_5bsQ24gi-VGF7g7?usp=sharing)

League-wide xG analytics on Sofascore data. KMeans archetypes, tactical radar, Poisson xPts, decomposition into finishing and defending, goal sources, shot maps, rolling form, bump charts.

**notebook_02_hero.png**

[Full sub-README](notebooks/02_team_analytics.md)

### 03 - Player Analytics

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1KGek1qdDoax2bLRj304S-fehQ5f11iN6?usp=sharing)

Per-player demographics, percentile pizzas, shot maps and statistical similarity.

**notebook_03_hero.png**

[Full sub-README](notebooks/03_player_analytics.md)

## Power BI dashboard

Executive-friendly view of the same data layer. Three pages, drag-and-drop interactivity for non-technical staff (coaches, scouts).

**1. League overview** - xPts standings table + Pts vs xPts horizontal bar chart with red-green gradient on the gap.

**powerbi_overview.png**

**2. Player over and under-performance** - Top 20 strikers ranked by Goals minus xG (finishing skill) + Top 10 goalkeepers ranked by goals prevented (shot-stopping skill).

**powerbi_player_overunder.png**

**3. Player Explorer** - Sortable per-player table with slicers (role, team, age range, minutes range). Recruiters can drill down to any subset in seconds.

**powerbi_player_explorer.png**

Source: `data/processed/powerbi/` CSVs, pre-computed by `scripts/12_export_powerbi.py` (Poisson xPts and H2H tie-break done in pandas so Power BI only renders).

## Data

| Source | What | Anti-bot | Output |
|---|---|---|---|
| Sofascore | xG per shot, per-match team stats, per-player advanced metrics for all 306 matches | Akamai Bot Manager | `data/processed/sofascore/` |
| FBref | Counting stats per club + 14-season historical results with closing bookmaker odds | Cloudflare | `data/processed/fbref/` |

FBref does not include the Opta-feed metrics for Ekstraklasa - no xG, no xA, no progressive carries. Every advanced metric in this project comes from the Sofascore scrape.

## Sofascore scraping - the engineering story

FBref blocks direct requests with Cloudflare. Sofascore blocks them with Akamai Bot Manager. Both fall to the same trick: drive a real Chrome instance over the Chrome DevTools Protocol and let the site's own SPA do the trusted API calls.

For FBref the Cloudflare challenge clears on first navigation and Playwright can pull HTML from any subsequent page.

Sofascore is harder. Every direct hit to `api.sofascore.com` returns 403 with `{"reason":"challenge"}`. Verified failing methods: plain `requests`, `curl_cffi` with Chrome131 TLS, in-page `fetch()`, even direct browser navigation to the JSON endpoint. The scraper does not call the API at all. It navigates the SPA pages and captures every `api.sofascore.com` JSON response the SPA emits via `page.on("response")`.

Five concrete problems along the way:

| Problem | Symptom | Solution |
|---|---|---|
| Wrong default season | SPA defaults to 2026/27 instead of 2025/26 | Programmatic click on the season dropdown |
| Lazy-loaded widgets | Shotmap, statistics and lineups not in initial DOM | Click `Statistics` and `Lineups` tabs, JS scroll, then capture |
| `asyncio.CancelledError` flood | Hundreds of errors during navigation | URL filter, read only the five wanted endpoints, swallow `BaseException` |
| Session blocked after ~130 requests | All subsequent matches return `missing ['ALL']` | Proactive re-prime every 50 events plus reactive re-prime on empty capture |
| One incomplete match after first pass | 305 of 306 finished matches | Re-run with `--skip-collect` flag - scraper is resumable |

Final scrape: 306 finished matches, five JSON files each (event, shotmap, statistics, lineups, incidents), persisted under `data/raw/sofascore/event_{id}/`.

Code: `scripts/08_sofascore_discover.py` (probe), `scripts/09_scrape_sofascore.py` (full scrape, resumable), `scripts/10_clean_sofascore.py` (JSON to CSV), `scripts/11_build_player_master.py` (season aggregates).
