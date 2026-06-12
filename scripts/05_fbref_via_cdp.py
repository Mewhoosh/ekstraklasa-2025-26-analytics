"""Connect to a manually-launched Chrome via CDP and fetch FBref Ekstraklasa data.

Setup before running:

1. Close all Chrome windows:
       taskkill /F /IM chrome.exe /T

2. Launch Chrome with a debug port and a dedicated profile (copy-paste in PowerShell):
       & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" `
           --remote-debugging-port=9222 `
           --user-data-dir="$env:USERPROFILE\\chrome_debug_profile"

3. In that Chrome window visit:
       https://fbref.com/en/comps/36/Ekstraklasa-Stats
   Solve the Cloudflare challenge once (one click). Page should show the league table.

4. Then run:
       python scripts/05_fbref_via_cdp.py
"""

from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9222"
LEAGUE_URL = "https://fbref.com/en/comps/36/Ekstraklasa-Stats"

TARGET_TEAMS = {"Jagiellonia", "Lech Poznan", "Legia"}


def main() -> None:
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"Cannot connect to Chrome on {CDP_URL}: {e}")
            print("Did you launch Chrome with --remote-debugging-port=9222 ?")
            return

        contexts = browser.contexts
        if not contexts:
            print("No browser contexts - Chrome is running but with no profile?")
            return

        context = contexts[0]
        page = context.new_page()

        # Probe the league page
        print(f"GET {LEAGUE_URL}")
        page.goto(LEAGUE_URL, wait_until="domcontentloaded", timeout=45_000)

        title = page.title()
        body = page.content()
        challenged = "just a moment" in title.lower()
        print(f"  title: {title}")
        print(f"  size:  {len(body):,} chars")
        print(f"  Cloudflare challenge: {'YES (please solve in the browser)' if challenged else 'no'}")
        print(f"  has Ekstraklasa data: {'Ekstraklasa' in body}")

        if challenged:
            print("\nSolve the challenge in the Chrome window, then re-run this script.")
            page.close()
            return

        # If unlocked, extract team links from the standings table
        print("\nExtracting team links from league page...")
        links = page.eval_on_selector_all(
            "table#results2025-2026361_overall a[href^='/en/squads/']",
            "els => els.map(e => ({name: e.innerText, href: e.href}))",
        )
        if not links:
            # Try a more generic selector if the table id changes
            links = page.eval_on_selector_all(
                "a[href^='/en/squads/']",
                "els => els.map(e => ({name: e.innerText, href: e.href}))",
            )

        print(f"  found {len(links)} squad links")
        seen = set()
        for item in links:
            name = item["name"].strip()
            href = item["href"]
            if name and name not in seen:
                seen.add(name)
                marker = " <-- TARGET" if name in TARGET_TEAMS else ""
                print(f"  {name:<30}  {href}{marker}")

        page.close()


if __name__ == "__main__":
    main()
