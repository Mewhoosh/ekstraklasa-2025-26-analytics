"""Probe FBref Ekstraklasa with Playwright (headless Chromium).

If headless passes Cloudflare automatically we can scrape without the manual
CDP+real-Chrome dance the Premier League project needed.

Usage:
    python -m pip install playwright
    python -m playwright install chromium
    python scripts/04_test_playwright.py
"""

from playwright.sync_api import sync_playwright


URLS = [
    "https://fbref.com/en/comps/36/Ekstraklasa-Stats",
    "https://fbref.com/en/squads/4f7b798d/Jagiellonia-Stats",
]


def probe(page, url: str) -> None:
    print(f"\nGET {url}")
    try:
        resp = page.goto(url, wait_until="domcontentloaded", timeout=45_000)
    except Exception as e:
        print(f"  navigation error: {e}")
        return

    status = resp.status if resp else "?"
    title = page.title()
    body = page.content()
    print(f"  status: {status}")
    print(f"  title:  {title}")
    print(f"  size:   {len(body):,} chars")

    challenged = "just a moment" in title.lower() or "cf-challenge" in body.lower()
    has_data = "Ekstraklasa" in body and not challenged
    print(f"  Cloudflare challenge: {'YES (blocked)' if challenged else 'no'}")
    print(f"  has Ekstraklasa data: {'YES' if has_data else 'no'}")


def main() -> None:
    with sync_playwright() as pw:
        # Headless Chromium with a realistic user-agent; Playwright auto-handles many cf checks
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = context.new_page()
        for url in URLS:
            probe(page, url)
        browser.close()


if __name__ == "__main__":
    main()
