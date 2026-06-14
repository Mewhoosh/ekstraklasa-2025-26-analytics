"""Sofascore discovery probe for Ekstraklasa 2025-26 (response-interception model).

Why this approach:
- api.sofascore.com sits behind Akamai Bot Manager. Any caller that hits the
  API directly - plain requests, curl_cffi (chrome131 TLS), even an in-page
  fetch() or a direct browser navigation - gets HTTP 403 {"reason":"challenge"}.
  All four were verified to fail.
- The Sofascore SPA itself loads data fine in the same browser. Akamai only
  trusts the requests the SPA fires from its own pages.
- So we do NOT call the API ourselves. We navigate the Chrome-on-:9222 browser
  to Sofascore pages and capture the api.sofascore.com JSON responses the SPA
  makes via page.on("response"). Guaranteed to work wherever the site works.

Goal - run ONCE before building the full scraper:
1. Capture the Ekstraklasa season list -> find the 2025-26 season id.
2. Capture the events list -> pick one finished match.
3. Open that match page -> capture its shotmap.
4. Confirm xG is present per shot. This is the make-or-break field.

Setup (same Chrome as FBref):
1. taskkill /F /IM chrome.exe /T
2. Launch:
     & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" `
         --remote-debugging-port=9222 `
         --user-data-dir="$env:USERPROFILE\\chrome_debug_profile"
3. python scripts/08_sofascore_discover.py

Outputs:
    data/raw/sofascore/discover_*.json - captured payloads for inspection.
"""

import json
import re
import time
from pathlib import Path

RAW = Path(__file__).parent.parent / "data" / "raw" / "sofascore"
RAW.mkdir(parents=True, exist_ok=True)

CDP_URL = "http://localhost:9222"

# Ekstraklasa unique-tournament id on Sofascore (from the site URL .../ekstraklasa/202).
TOURNAMENT_ID = 202
TOURNAMENT_URL = "https://www.sofascore.com/tournament/football/poland/ekstraklasa/202"


class SofascoreHarvester:
    """Drive the CDP Chrome and capture api.sofascore.com JSON responses."""

    def __init__(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise SystemExit("pip install playwright && playwright install chromium")

        self.pw = sync_playwright().start()
        try:
            browser = self.pw.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            raise SystemExit(
                f"Cannot connect to Chrome on {CDP_URL}: {e}\n"
                "Launch Chrome with --remote-debugging-port=9222 first (see docstring)."
            )
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        self.page = ctx.new_page()
        self.captured: dict[str, str] = {}
        self.page.on("response", self._on_response)

    def _on_response(self, response) -> None:
        url = response.url
        if "/api/v1/" not in url:
            return
        if response.status != 200:
            return
        try:
            body = response.text()
        except Exception:
            return
        if not body or body.lstrip()[:1] not in "{[":
            return
        # Skip Akamai challenge bodies that still return 200 in odd cases.
        if '"reason"' in body[:120] and "challenge" in body[:120]:
            return
        self.captured[url] = body

    def visit(self, url: str, settle_seconds: float = 4.0) -> None:
        print(f"\n  navigate {url}")
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as e:
            print(f"    nav note: {e}")
        self._simulate_human()
        time.sleep(settle_seconds)

    def _simulate_human(self) -> None:
        try:
            for x, y in [(300, 300), (700, 450), (500, 700)]:
                self.page.mouse.move(x, y)
                time.sleep(0.15)
            self.page.mouse.wheel(0, 1400)
            time.sleep(0.4)
            self.page.mouse.wheel(0, 1400)
            time.sleep(0.4)
            self.page.mouse.wheel(0, -800)
            time.sleep(0.3)
        except Exception:
            pass

    def find(self, *substrings: str) -> dict | None:
        """Return the parsed JSON of the first captured URL matching all substrings."""
        for url, body in self.captured.items():
            if all(s in url for s in substrings):
                try:
                    return json.loads(body)
                except Exception:
                    continue
        return None

    def find_url(self, *substrings: str) -> str | None:
        for url in self.captured:
            if all(s in url for s in substrings):
                return url
        return None

    def click_text(self, text: str, exact: bool = True) -> bool:
        """Real Playwright click (dispatches full mouse events, unlike el.click())."""
        try:
            self.page.get_by_text(text, exact=exact).first.click(timeout=6000)
            return True
        except Exception as e:
            print(f"    click_text({text!r}) failed: {str(e)[:80]}")
            return False

    def _js_scroll(self, y: int) -> None:
        try:
            self.page.evaluate("(y) => window.scrollTo(0, y)", y)
        except Exception:
            pass

    def harvest_until(self, *substrings: str, max_seconds: float = 30.0) -> dict | None:
        """Scroll the window (via JS) in steps until an endpoint matching all
        substrings is captured, or timeout. Triggers lazy-loaded widgets."""
        deadline = time.time() + max_seconds
        i = 0
        while time.time() < deadline:
            hit = self.find(*substrings)
            if hit:
                return hit
            # Sweep down the page then back up to force lazy widgets into view.
            self._js_scroll((i % 8) * 700)
            i += 1
            time.sleep(1.2)
        return self.find(*substrings)

    def find_finished_events(self):
        """Scan captured round/last feeds for one that contains finished
        matches. Returns (season_id, feed_json, finished_events)."""
        for url, body in self.captured.items():
            if "/events/round" not in url and "/events/last" not in url:
                continue
            try:
                d = json.loads(body)
            except Exception:
                continue
            evs = d.get("events", [])
            fin = [e for e in evs if (e.get("status") or {}).get("type") == "finished"]
            if fin:
                m = re.search(r"season/(\d+)/", url)
                return (int(m.group(1)) if m else None, d, fin)
        return (None, None, [])

    def close(self) -> None:
        try:
            self.page.close()
        finally:
            self.pw.stop()


def save(name: str, payload) -> None:
    path = RAW / f"discover_{name}.json"
    if isinstance(payload, (dict, list)):
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        path.write_text(str(payload), encoding="utf-8")
    print(f"    saved -> {path.name} ({path.stat().st_size:,} bytes)")


def _season_id_from_urls(h: "SofascoreHarvester") -> int | None:
    """Pull the season id out of any captured .../season/{id}/... URL."""
    for url in h.captured:
        m = re.search(rf"unique-tournament/{TOURNAMENT_ID}/season/(\d+)/", url)
        if m:
            return int(m.group(1))
    return None


def _all_season_ids(h: "SofascoreHarvester") -> set[int]:
    ids = set()
    for url in h.captured:
        m = re.search(rf"unique-tournament/{TOURNAMENT_ID}/season/(\d+)/", url)
        if m:
            ids.add(int(m.group(1)))
    return ids


def pick_season_2025_26(seasons: list[dict]) -> dict | None:
    for s in seasons:
        if str(s.get("year")).strip() in {"25/26", "2025/2026", "2025-2026"}:
            return s
    for s in seasons:
        name = str(s.get("name", "")).lower()
        if any(tag in name for tag in ("25/26", "2025/2026", "2025-2026")):
            return s
    return None


def main() -> None:
    h = SofascoreHarvester()
    try:
        # Step 1: tournament page. The SPA fires seasons + standings + events.
        print("[1] harvesting Ekstraklasa tournament page")
        h.visit(TOURNAMENT_URL, settle_seconds=5)
        print(f"    captured {len(h.captured)} api responses so far")
        for url in sorted(h.captured):
            print(f"      - {url.split('/api/v1/')[-1]}")

        # The active season the SPA loads by default is the UPCOMING one
        # (2026-27). We want the finished 2025-26 season.
        active_id = _season_id_from_urls(h)
        print(f"\n    default (upcoming) season the SPA loaded: {active_id}")

        # Go to the matches tab, open the season dropdown with a real click,
        # then click the 25/26 option. We read the resulting season id from
        # whatever events feed comes back containing finished matches.
        print("\n[1b] switching to the 2025-26 season via the dropdown")
        h.visit(f"{TOURNAMENT_URL}#id:{active_id},tab:matches", settle_seconds=3)
        h.click_text("26/27")          # open dropdown (current label)
        time.sleep(1.5)
        h.click_text("25/26")          # select 2025-26
        time.sleep(4)
        h._simulate_human()
        time.sleep(2)

        # The dropdown switch makes the SPA load 2025-26 data under a new season
        # id (standings/rounds for it appear in captured URLs). Find that id -
        # it is the season id that is not the upcoming one.
        other_ids = sorted(_all_season_ids(h) - {active_id})
        print(f"    season ids seen besides upcoming: {other_ids}")
        season_id = other_ids[-1] if other_ids else None

        if season_id:
            print(f"\n>>> 2025-26 season_id={season_id}; loading its matches tab")
            h.visit(f"{TOURNAMENT_URL}#id:{season_id},tab:matches", settle_seconds=5)

        sid2, events_data, events = h.find_finished_events()
        season_id = sid2 or season_id
        if not events_data:
            print("    no finished-events feed captured automatically.")
            print("    FALLBACK: in the debug Chrome, switch the season dropdown")
            print("    to 25/26 yourself and click any finished match, then re-run.")
            _dump_all(h)
            return
        print(f"\n>>> resolved 2025-26 season_id={season_id}")
        save("02_events", events_data)
        finished = [e for e in events if (e.get("status") or {}).get("type") == "finished"]
        print(f"    {len(events)} events, {len(finished)} finished")

        if not finished:
            print("!!! no finished events in this feed page")
            return
        event = finished[-1]
        eid = event["id"]
        home = event.get("homeTeam", {})
        away = event.get("awayTeam", {})
        hs = (event.get("homeScore") or {}).get("current")
        as_ = (event.get("awayScore") or {}).get("current")
        print(f"\n>>> sample event {eid}: {home.get('name')} {hs}-{as_} {away.get('name')}")

        # Step 3: match page -> shotmap with xG.
        print("\n[3] harvesting match page for shotmap")
        slug = f"{home.get('slug','home')}-{away.get('slug','away')}"
        custom = event.get("customId", "")
        match_url = f"https://www.sofascore.com/football/match/{slug}/{custom}#id:{eid}"
        h.visit(match_url, settle_seconds=4)

        # The SPA only fires shotmap/statistics/lineups when their widgets/tabs
        # become active. Click the tabs and JS-scroll to trigger them.
        for tab in ("Statistics", "Lineups"):
            if h.click_text(tab):
                print(f"    clicked '{tab}' tab")
                time.sleep(2.5)
        print("    scrolling to trigger lazy-loaded shotmap ...")
        shot_data = h.harvest_until(f"event/{eid}/shotmap", max_seconds=30)
        if not shot_data:
            print("    shotmap could not be captured.")
            print("    FALLBACK: in the debug Chrome open this match, scroll to the")
            print(f"    'Shot map' section, then re-run:\n    {match_url}")
            _dump_all(h)
            return
        save(f"03_shotmap_{eid}", shot_data)

        shots = shot_data.get("shotmap") or shot_data.get("shots") or []
        print(f"\n[4] shotmap inspection: {len(shots)} shots")
        if shots:
            print(f"    shot fields: {sorted(shots[0].keys())}")
            xgs = [s.get("xg") for s in shots]
            non_null = [x for x in xgs if x is not None]
            print(f"    xG present on {len(non_null)}/{len(shots)} shots")
            if non_null:
                print(f"    sample xG: {non_null[:6]}")
                print("\n    >>> CONFIRMED: Sofascore exposes xG per shot for Ekstraklasa <<<")
            else:
                print("\n    >>> xG is null - pivot to API-Football (see PROJECT_PLAN_v2.md) <<<")

        # also grab a few sibling endpoints for the scraper design (via capture)
        for name in ("statistics", "lineups", "incidents"):
            data = h.find(f"event/{eid}/{name}") or h.harvest_until(f"event/{eid}/{name}", max_seconds=8)
            if data:
                save(f"03_{name}_{eid}", data)
                print(f"    bonus: captured event {name}")
            else:
                print(f"    (event {name} not captured)")

        print("\n=== SUMMARY ===")
        print(f"tournament_id = {TOURNAMENT_ID}")
        print(f"season_id     = {season_id}")
        print(f"sample event  = {eid}")
        print(f"raw payloads  -> {RAW}")
    finally:
        h.close()


def _dump_all(h: SofascoreHarvester) -> None:
    print("\n    --- all captured api endpoints ---")
    for url in sorted(h.captured):
        print(f"      {url}")
    if h.captured:
        save("99_all_urls", sorted(h.captured.keys()))


if __name__ == "__main__":
    main()
