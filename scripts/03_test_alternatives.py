"""Probe two alternative paths to richer data:

1. cloudscraper on FBref (Python lib that solves Cloudflare JS challenges).
2. Sofascore JSON API endpoints (often less protected than HTML pages).

If either works we save the heavy CDP+real-Chrome setup the Premier League project needed.
"""

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
}


def test_cloudscraper_fbref() -> None:
    print("\n--- Test 1: cloudscraper on FBref ---")
    try:
        import cloudscraper
    except ImportError:
        print("  cloudscraper not installed. Run: python -m pip install cloudscraper")
        return

    scraper = cloudscraper.create_scraper()
    try:
        r = scraper.get("https://fbref.com/en/comps/36/Ekstraklasa-Stats", timeout=60)
        print(f"  status: {r.status_code}")
        print(f"  size:   {len(r.text):,} chars")
        has_data = "Ekstraklasa" in r.text and "Just a moment" not in r.text
        print(f"  passed Cloudflare: {'YES' if has_data else 'NO'}")
        if has_data:
            print(f"  contains 'Jagiellonia': {'Jagiellonia' in r.text}")
            print(f"  contains 'Lech Poznan': {'Lech' in r.text}")
    except Exception as e:
        print(f"  ERROR: {e}")


def test_sofascore_api() -> None:
    print("\n--- Test 2: Sofascore JSON API ---")
    # Sofascore tournament ID for Ekstraklasa - 202 according to research, but let's verify
    # The "season" endpoint gives season metadata and ID for 2025-26
    probes = [
        # League seasons list
        ("https://api.sofascore.com/api/v1/unique-tournament/202/seasons", "League seasons"),
        # Standings for season (need to find season ID first, this might 404)
        ("https://api.sofascore.com/api/v1/unique-tournament/202/info", "League info"),
    ]
    for url, label in probes:
        print(f"\n  {label}")
        print(f"  GET {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            print(f"    status: {r.status_code}")
            print(f"    size:   {len(r.text):,} chars")
            if r.status_code == 200:
                # Try to parse as JSON
                try:
                    j = r.json()
                    keys = list(j.keys()) if isinstance(j, dict) else "list"
                    print(f"    JSON keys: {keys}")
                    print(f"    preview: {str(j)[:300]}")
                except Exception:
                    print(f"    not JSON, preview: {r.text[:200]}")
            else:
                preview = r.text[:200].replace("\n", " ")
                print(f"    preview: {preview}")
        except Exception as e:
            print(f"    ERROR: {e}")


def main() -> None:
    test_cloudscraper_fbref()
    test_sofascore_api()


if __name__ == "__main__":
    main()
