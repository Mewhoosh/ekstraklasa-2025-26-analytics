"""Probe whether FBref Ekstraklasa pages are accessible with a simple requests call.

The Premier League scraping work in another project needed Chrome DevTools Protocol
because of Cloudflare Turnstile. This script checks whether Ekstraklasa pages on the
same domain are equally locked down or open enough for a plain request.
"""

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

PROBES = [
    # Main league page (results, fixtures, standings)
    "https://fbref.com/en/comps/36/Ekstraklasa-Stats",
    # Single club page (Jagiellonia 2025-26 squad stats)
    "https://fbref.com/en/squads/4f7b798d/Jagiellonia-Stats",
]


def probe(url: str) -> None:
    print(f"\nGET {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except Exception as e:
        print(f"  ERROR: {e}")
        return

    print(f"  status: {r.status_code}")
    print(f"  size:   {len(r.text):,} chars")

    if r.status_code == 200:
        markers = {
            "Ekstraklasa": "Ekstraklasa" in r.text,
            "Jagiellonia": "Jagiellonia" in r.text,
            "Standings table": 'id="results' in r.text,
            "Cloudflare challenge": "Just a moment" in r.text or "cf-challenge" in r.text.lower(),
        }
        for label, present in markers.items():
            print(f"  {label:<22} {'yes' if present else 'no'}")
    else:
        snippet = r.text[:400].replace("\n", " ")
        print(f"  body preview: {snippet}")


def main() -> None:
    for url in PROBES:
        probe(url)


if __name__ == "__main__":
    main()
