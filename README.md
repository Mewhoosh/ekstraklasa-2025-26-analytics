# Ekstraklasa 2025/26 Analytics

[![Streamlit](https://img.shields.io/badge/Open%20in-Streamlit-FF4B4B?logo=streamlit&logoColor=white&style=for-the-badge)](https://ekstraklasa-2025-26-analytics.streamlit.app/)
[![Notebook 01](https://img.shields.io/badge/Sub--README-Notebook%2001-1f6feb?style=for-the-badge&logo=markdown&logoColor=white)](notebooks/01_three_clubs_analysis.md)
[![Notebook 02](https://img.shields.io/badge/Sub--README-Notebook%2002-1f6feb?style=for-the-badge&logo=markdown&logoColor=white)](notebooks/02_team_analytics.md)
[![Notebook 03](https://img.shields.io/badge/Sub--README-Notebook%2003-1f6feb?style=for-the-badge&logo=markdown&logoColor=white)](notebooks/03_player_analytics.md)
[![Colab 01](https://img.shields.io/badge/Colab-Notebook%2001-F9AB00?logo=googlecolab&logoColor=white&style=for-the-badge)](https://colab.research.google.com/drive/1WkE71OOVvHdRSHehyfqPhypmKhN91K0A?usp=sharing)
[![Colab 02](https://img.shields.io/badge/Colab-Notebook%2002-F9AB00?logo=googlecolab&logoColor=white&style=for-the-badge)](https://colab.research.google.com/drive/1QopjjtC60sVqMAck_5bsQ24gi-VGF7g7?usp=sharing)
[![Colab 03](https://img.shields.io/badge/Colab-Notebook%2003-F9AB00?logo=googlecolab&logoColor=white&style=for-the-badge)](https://colab.research.google.com/drive/1KGek1qdDoax2bLRj304S-fehQ5f11iN6?usp=sharing)

End-to-end analytics on the Polish top flight 2025/26 season. Multi-source scraping behind two anti-bot stacks, xG-based modelling, team-style clustering, season-long form trajectories, per-player percentile analysis and a multi-page Streamlit app on top of everything.

| Layer | Tech |
|---|---|
| Scraping | Playwright + Chrome DevTools Protocol |
| Cleaning | pandas |
| Analysis | Jupyter |
| App | Streamlit + Plotly |
| BI | Power BI |

## Streamlit app

[![Streamlit](https://img.shields.io/badge/Open%20in-Streamlit-FF4B4B?logo=streamlit&logoColor=white&style=for-the-badge)](https://ekstraklasa-2025-26-analytics.streamlit.app/)

The main artifact. Five pages plus a rich home overview. Reads directly from `data/processed/`.


| Page | What it shows |
|---|---|
| **Home / League overview** | Headline KPIs, xPts standings, Pts vs xPts scatter, position by matchweek bump chart, xPts breakdown heatmap, KMeans style clusters, records and extremes tabs. |
| **Club Profile** | Pick a club. Headline metrics, actual vs expected trajectory, rolling 5-match xG/xGA, team shot map, goal sources by situation, match log, top contributors and per-club records and extremes. |
| **Head-to-Head** | Pick any two clubs. Direct meetings table, style fingerprint radar, cumulative points, rolling xG comparison, shot maps side by side. |
| **Player Explorer** | Filter by team / role / minutes / age / market value. Pick a player and see their pizza, shot map and match-by-match performance trend. |
| **Player Compare** | Two modes (Outfield / GK). Side-by-side pizzas, shot maps and per-90 stat comparison. |
| **Scouting Tool** | Cosine similarity on the per-90 vector. Filter by MV cap, age window and same-team exclusion. Returns role-matched candidates only. |

### Home / League overview

The whole league in one scroll - standings, scatter, bump chart, archetypes and records, all on a single page.

<img width="1498" height="695" alt="obraz" src="https://github.com/user-attachments/assets/c60ca05b-0e4b-4f6c-a503-6faf81f433a6" />

<img width="1496" height="652" alt="obraz" src="https://github.com/user-attachments/assets/3663f75b-e239-442e-b989-1da6dce3d873" />

<img width="1522" height="681" alt="obraz" src="https://github.com/user-attachments/assets/975b1d39-1c4e-473e-ae88-0bea613ca4f4" />

### Club Profile

Single-club deep dive. Useful for opponent prep or a season post-mortem on any of the 18 sides.

<img width="1651" height="763" alt="obraz" src="https://github.com/user-attachments/assets/ec02b80b-5d9e-4f11-9285-0a7d14e5e454" />

<img width="1460" height="604" alt="obraz" src="https://github.com/user-attachments/assets/2811992f-3a33-4cee-9e85-058ac404c420" />

<img width="1523" height="249" alt="obraz" src="https://github.com/user-attachments/assets/be954f3a-0d49-42eb-977d-b4b0a592249c" />

### Head-to-Head

Compare any two clubs. Direct meetings, style overlap and where the trajectories pulled apart.

<img width="1585" height="733" alt="obraz" src="https://github.com/user-attachments/assets/909fec9e-b443-4cf3-91cf-78bfb69e9e82" />

<img width="1512" height="873" alt="obraz" src="https://github.com/user-attachments/assets/ed7d261b-a80b-4d31-b2d6-ad038bf9d460" />



### Player Explorer

Search the whole league by filters, drill into a single player profile.

<img width="1452" height="882" alt="obraz" src="https://github.com/user-attachments/assets/d7dcb785-a818-410e-8853-f12381bc44c7" />


### Player Compare

Pick any two players. Outfield or GK mode. Side-by-side pizzas, shot maps and per-90 stats.

<img width="1481" height="871" alt="obraz" src="https://github.com/user-attachments/assets/809f3511-3137-4122-b741-1282e217a290" />


### Scouting Tool

Cosine similarity on the per-90 vector. Pick a target, set filters, get role-matched candidates only - pick a defender, get defenders.

<img width="1523" height="819" alt="obraz" src="https://github.com/user-attachments/assets/ba8bb1ef-e11c-4a72-9f2c-85b300af9a4e" />


### Run locally

```powershell
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Notebooks

Three Jupyter notebooks. Each has a companion sub-README with the full chart gallery.

### 01 - Three Clubs Analysis

[![Sub-README](https://img.shields.io/badge/Sub--README-Notebook%2001-1f6feb?style=for-the-badge&logo=markdown&logoColor=white)](notebooks/01_three_clubs_analysis.md)
[![Colab](https://img.shields.io/badge/Open%20in-Colab-F9AB00?logo=googlecolab&logoColor=white&style=for-the-badge)](https://colab.research.google.com/drive/1WkE71OOVvHdRSHehyfqPhypmKhN91K0A?usp=sharing)

Comparative analysis of Lech, Jaga and Legia on FBref counting stats. Season trajectory, form, splits, head-to-head, key players, goalkeeper rotation story. **Limited scope** - this notebook predates the Sofascore scrape and runs on counting stats only. Notebooks 02 and 03 are the xG-enabled versions.

<img width="1174" height="550" alt="obraz" src="https://github.com/user-attachments/assets/d0129f03-bc62-4913-bbbf-e64ff4d94c70" />


### 02 - Team Analytics

[![Sub-README](https://img.shields.io/badge/Sub--README-Notebook%2002-1f6feb?style=for-the-badge&logo=markdown&logoColor=white)](notebooks/02_team_analytics.md)
[![Colab](https://img.shields.io/badge/Open%20in-Colab-F9AB00?logo=googlecolab&logoColor=white&style=for-the-badge)](https://colab.research.google.com/drive/1QopjjtC60sVqMAck_5bsQ24gi-VGF7g7?usp=sharing)

League-wide xG analytics on Sofascore data. KMeans archetypes, tactical radar, Poisson xPts, decomposition into finishing and defending, goal sources, shot maps, rolling form, bump charts.

<img width="1746" height="790" alt="obraz" src="https://github.com/user-attachments/assets/ffc6e3c2-414e-40e3-948b-193f795f62ed" />


### 03 - Player Analytics

[![Sub-README](https://img.shields.io/badge/Sub--README-Notebook%2003-1f6feb?style=for-the-badge&logo=markdown&logoColor=white)](notebooks/03_player_analytics.md)
[![Colab](https://img.shields.io/badge/Open%20in-Colab-F9AB00?logo=googlecolab&logoColor=white&style=for-the-badge)](https://colab.research.google.com/drive/1KGek1qdDoax2bLRj304S-fehQ5f11iN6?usp=sharing)

Per-player demographics, percentile pizzas, shot maps and statistical similarity.

<img width="1749" height="1301" alt="obraz" src="https://github.com/user-attachments/assets/cebcb65e-f751-4f94-bddc-58ff53afb92b" />

<img width="2189" height="1194" alt="obraz" src="https://github.com/user-attachments/assets/14b4ebaa-d3ce-48df-b433-e96f55b3be1b" />

## Power BI dashboard

Executive-friendly view of the same data layer. Three pages, drag-and-drop interactivity for non-technical staff (coaches, scouts).

**1. League overview** - xPts standings table + Pts vs xPts horizontal bar chart with red-green gradient on the gap.

<img width="1311" height="735" alt="obraz" src="https://github.com/user-attachments/assets/54a50f2e-1902-491e-bf96-7ef1887674e7" />

**2. Player over and under-performance** - Top 20 strikers ranked by Goals minus xG (finishing skill) + Top 10 goalkeepers ranked by goals prevented (shot-stopping skill).

<img width="1309" height="736" alt="obraz" src="https://github.com/user-attachments/assets/8f989862-326b-40e2-b3e9-dacb483f234e" />


**3. Player Explorer** - Sortable per-player table with slicers (role, team, age range, minutes range). Recruiters can drill down to any subset in seconds.

<img width="1229" height="729" alt="obraz" src="https://github.com/user-attachments/assets/fcbcb23e-d03c-49bd-b57c-affc7bdc703d" />


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

---

[![Streamlit](https://img.shields.io/badge/Open%20in-Streamlit-FF4B4B?logo=streamlit&logoColor=white&style=for-the-badge)](https://ekstraklasa-2025-26-analytics.streamlit.app/)
[![Notebook 01](https://img.shields.io/badge/Sub--README-Notebook%2001-1f6feb?style=for-the-badge&logo=markdown&logoColor=white)](notebooks/01_three_clubs_analysis.md)
[![Notebook 02](https://img.shields.io/badge/Sub--README-Notebook%2002-1f6feb?style=for-the-badge&logo=markdown&logoColor=white)](notebooks/02_team_analytics.md)
[![Notebook 03](https://img.shields.io/badge/Sub--README-Notebook%2003-1f6feb?style=for-the-badge&logo=markdown&logoColor=white)](notebooks/03_player_analytics.md)
[![Colab 01](https://img.shields.io/badge/Colab-Notebook%2001-F9AB00?logo=googlecolab&logoColor=white&style=for-the-badge)](https://colab.research.google.com/drive/1WkE71OOVvHdRSHehyfqPhypmKhN91K0A?usp=sharing)
[![Colab 02](https://img.shields.io/badge/Colab-Notebook%2002-F9AB00?logo=googlecolab&logoColor=white&style=for-the-badge)](https://colab.research.google.com/drive/1QopjjtC60sVqMAck_5bsQ24gi-VGF7g7?usp=sharing)
[![Colab 03](https://img.shields.io/badge/Colab-Notebook%2003-F9AB00?logo=googlecolab&logoColor=white&style=for-the-badge)](https://colab.research.google.com/drive/1KGek1qdDoax2bLRj304S-fehQ5f11iN6?usp=sharing)
