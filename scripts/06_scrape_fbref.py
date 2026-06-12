"""Scrape FBref Ekstraklasa 2025-26 via the CDP-attached Chrome instance.

Run after Chrome is already up with --remote-debugging-port=9222 and the league
page has been unlocked (see scripts/05_fbref_via_cdp.py for setup).

Saves:
- Raw HTML of every fetched page (data/raw/fbref_*.html) - backup, lets us
  re-parse offline without re-scraping.
- Every table on each page as a separate CSV (data/raw/fbref_*_table_NN.csv).
"""

import io
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9222"
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

PAGES = {
    "league":      "https://fbref.com/en/comps/36/Ekstraklasa-Stats",
    # Our three focus clubs first
    "jagiellonia": "https://fbref.com/en/squads/4f7b798d/Jagiellonia-Stats",
    "lech":        "https://fbref.com/en/squads/fdba14df/Lech-Poznan-Stats",
    "legia":       "https://fbref.com/en/squads/a73408a7/Legia-Warsaw-Stats",
    # Remaining 15 clubs - needed for league-wide context, tactical fingerprint
    # vs league average, and clustering analyses.
    "gornik_zabrze":   "https://fbref.com/en/squads/d2f21b23/Gornik-Zabrze-Stats",
    "rakow":           "https://fbref.com/en/squads/e0b3aa47/Rakow-Czestochowa-Stats",
    "gks_katowice":    "https://fbref.com/en/squads/6c2f28fd/Katowice-Stats",
    "zaglebie_lubin":  "https://fbref.com/en/squads/3458af25/Zaglebie-Lubin-Stats",
    "wisla_plock":     "https://fbref.com/en/squads/fe423bcc/Wisla-Plock-Stats",
    "pogon_szczecin":  "https://fbref.com/en/squads/8a3f95b9/Pogon-Szczecin-Stats",
    "radomiak_radom":  "https://fbref.com/en/squads/3b58a049/Radomiak-Radom-Stats",
    "korona_kielce":   "https://fbref.com/en/squads/eae6c5ae/Korona-Kielce-Stats",
    "motor_lublin":    "https://fbref.com/en/squads/dd772731/Motor-Lublin-Stats",
    "cracovia":        "https://fbref.com/en/squads/6e7c9b0b/Cracovia-Stats",
    "widzew_lodz":     "https://fbref.com/en/squads/2232debd/Widzew-Lodz-Stats",
    "piast_gliwice":   "https://fbref.com/en/squads/ad2649a5/Piast-Gliwice-Stats",
    "lechia_gdansk":   "https://fbref.com/en/squads/5d36c8f0/Lechia-Gdansk-Stats",
    "arka_gdynia":     "https://fbref.com/en/squads/d51bc6dd/Arka-Gdynia-Stats",
    "termalica":       "https://fbref.com/en/squads/179c2bdf/Bruk-Bet-Termalica-Nieciecza-Stats",
}


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower())
    return s.strip("_")[:60] or "table"


def extract_tables(html: str) -> list[tuple[str, pd.DataFrame]]:
    """Return (caption_or_id, dataframe) for every table on the page.

    FBref hides several tables inside HTML comments so the rendered DOM does not
    expose them to pd.read_html. Stripping the comment markers makes them visible.
    """
    cleaned = html.replace("<!--", "").replace("-->", "")
    try:
        tables = pd.read_html(io.StringIO(cleaned))
    except ValueError:
        return []

    # Pull captions / table ids from the cleaned HTML for naming hints
    ids = re.findall(r'<table[^>]*id="([^"]+)"', cleaned)
    captions = re.findall(r"<caption[^>]*>(.*?)</caption>", cleaned, flags=re.DOTALL)
    labels: list[str] = []
    for i, df in enumerate(tables):
        if i < len(captions):
            label = re.sub(r"<[^>]+>", "", captions[i]).strip()
        elif i < len(ids):
            label = ids[i]
        else:
            label = f"table_{i:02d}"
        labels.append(label or f"table_{i:02d}")
    return list(zip(labels, tables))


def save_page(name: str, html: str, tables: Iterable[tuple[str, pd.DataFrame]]) -> None:
    html_path = RAW_DIR / f"fbref_{name}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  saved html -> {html_path.name}")

    for i, (label, df) in enumerate(tables):
        slug = slugify(label)
        out = RAW_DIR / f"fbref_{name}_{i:02d}_{slug}.csv"
        try:
            df.to_csv(out, index=False)
            print(f"    table {i:02d}: {df.shape[0]:>4} rows x {df.shape[1]:>3} cols -> {out.name}")
        except Exception as e:
            print(f"    table {i:02d}: save failed ({e})")


def main() -> None:
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"Cannot connect to Chrome on {CDP_URL}: {e}")
            return

        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        for name, url in PAGES.items():
            print(f"\nGET {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            except Exception as e:
                print(f"  navigation error: {e}")
                continue

            title = page.title()
            if "just a moment" in title.lower():
                print("  Cloudflare challenge - solve in the browser, then re-run")
                continue

            html = page.content()
            tables = extract_tables(html)
            print(f"  {len(tables)} tables found")
            save_page(name, html, tables)

        page.close()
        print(f"\nDone. Outputs in {RAW_DIR}")


if __name__ == "__main__":
    main()
