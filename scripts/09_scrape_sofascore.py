"""Full Sofascore scrape for Ekstraklasa 2025-26 via response interception.

Confirmed by scripts/08_sofascore_discover.py:
  tournament_id = 202
  season_id     = 76477   (2025-26; the SPA defaults to upcoming 96144)
  xG present on every shot; per-player advanced stats in lineups.

Why interception (not a direct API client):
  api.sofascore.com returns 403 (Akamai) to every non-SPA caller - plain
  requests, curl_cffi, in-page fetch, and direct navigation all fail. Only the
  requests the Sofascore SPA fires from its own pages get through. So we drive
  the manually-launched Chrome on :9222, navigate pages, and capture the
  api.sofascore.com JSON the SPA emits (page.on("response")).

Setup (same Chrome as FBref):
  1. taskkill /F /IM chrome.exe /T
  2. & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" `
         --remote-debugging-port=9222 `
         --user-data-dir="$env:USERPROFILE\\chrome_debug_profile"
  3. python scripts/09_scrape_sofascore.py

The run is RESUMABLE. Events whose raw JSON already exists are skipped, so you
can stop (Ctrl-C) and re-run any time.

Two phases:
  A. collect_events  - drive the round selector 1..34, capture each round's
     events, write data/raw/sofascore/events_index.json (306 matches).
  B. scrape_events   - per match, open the page, click Statistics + Lineups,
     scroll for the shotmap, save the 5 endpoints to
     data/raw/sofascore/event_{id}/{name}.json

Flags:
  --rounds 1-34        limit Phase A round range (default 1-34)
  --limit N            Phase B: only scrape the first N missing events
  --events-only        run Phase A only (build the index, no match scraping)
  --skip-collect       skip Phase A, reuse an existing events_index.json
"""

import argparse
import json
import re
import time
from pathlib import Path

RAW = Path(__file__).parent.parent / "data" / "raw" / "sofascore"
RAW.mkdir(parents=True, exist_ok=True)
EVENTS_INDEX = RAW / "events_index.json"

CDP_URL = "http://localhost:9222"
TOURNAMENT_ID = 202
SEASON_ID = 76477
TOURNAMENT_URL = "https://www.sofascore.com/tournament/football/poland/ekstraklasa/202"

# Per-event endpoints to persist. event/{id} itself plus these suffixes.
EVENT_PARTS = ["", "shotmap", "statistics", "lineups", "incidents"]


class Harvester:
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
        self._closing = False
        self.page.on("response", self._on_response)

    @staticmethod
    def _wanted(url: str) -> bool:
        # Only the endpoints we actually persist - keeps body reads (and the
        # cancellation noise that comes with them) to a minimum.
        if "/api/v1/" not in url:
            return False
        if "/events/round" in url or "/events/last" in url:
            return True
        return bool(re.search(r"/event/\d+(?:$|/shotmap|/statistics|/lineups|/incidents)", url))

    def _on_response(self, response) -> None:
        if self._closing:
            return
        url = response.url
        if not self._wanted(url) or response.status != 200:
            return
        try:
            body = response.text()
        except BaseException:
            # asyncio.CancelledError (BaseException) fires for in-flight
            # responses during navigation / shutdown - ignore quietly.
            return
        if not body or body.lstrip()[:1] not in "{[":
            return
        if '"reason"' in body[:120] and "challenge" in body[:120]:
            return
        self.captured[url] = body

    def visit(self, url: str, settle: float = 4.0) -> None:
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as e:
            print(f"    nav note: {str(e)[:80]}")
        self._human()
        time.sleep(settle)

    def _human(self) -> None:
        try:
            for x, y in [(300, 300), (700, 450), (500, 700)]:
                self.page.mouse.move(x, y)
                time.sleep(0.1)
        except Exception:
            pass

    def js_scroll(self, y: int) -> None:
        try:
            self.page.evaluate("(y) => window.scrollTo(0, y)", y)
        except Exception:
            pass

    def click_text(self, text: str, exact: bool = True) -> bool:
        try:
            self.page.get_by_text(text, exact=exact).first.click(timeout=5000)
            return True
        except Exception:
            return False

    def find(self, *subs: str) -> dict | None:
        for url, body in self.captured.items():
            if all(s in url for s in subs):
                try:
                    return json.loads(body)
                except Exception:
                    continue
        return None

    def harvest_until(self, *subs: str, max_seconds: float = 25.0) -> dict | None:
        deadline = time.time() + max_seconds
        i = 0
        while time.time() < deadline:
            hit = self.find(*subs)
            if hit:
                return hit
            self.js_scroll((i % 8) * 700)
            i += 1
            time.sleep(1.1)
        return self.find(*subs)

    def close(self) -> None:
        self._closing = True
        try:
            self.page.remove_listener("response", self._on_response)
        except Exception:
            pass
        try:
            self.page.close()
        except Exception:
            pass
        finally:
            try:
                self.pw.stop()
            except Exception:
                pass


def prime(h: Harvester) -> None:
    """Solve the Akamai cookie and switch the tournament view to 2025-26."""
    print("priming session ...")
    h.visit("https://www.sofascore.com/", settle=3)
    h.visit(f"{TOURNAMENT_URL}#id:96144,tab:matches", settle=3)
    h.click_text("26/27")
    time.sleep(1.5)
    h.click_text("25/26")
    time.sleep(3)
    h.visit(f"{TOURNAMENT_URL}#id:{SEASON_ID},tab:matches", settle=4)


def reprime(h: Harvester) -> None:
    """Refresh the Akamai cookie mid-run (it expires / gets rate-limited after
    ~100-130 requests, after which the SPA's own calls start returning 403 and
    nothing can be captured). Re-browsing the site renews the trusted cookie."""
    print("    >> re-priming session (Akamai cookie refresh) ...")
    h.visit("https://www.sofascore.com/", settle=4)
    h._human()
    h.visit(f"{TOURNAMENT_URL}#id:{SEASON_ID},tab:matches", settle=4)
    time.sleep(3)


def select_round(h: Harvester, n: int) -> bool:
    """Open the round selector and pick round n."""
    # Open: click whatever element currently shows "Round <k>".
    opened = h.page.evaluate(
        """
        () => {
            const re = /^Round\\s+\\d+$/;
            const els = Array.from(document.querySelectorAll('button, span, div, a'));
            for (const el of els) {
                if (re.test((el.textContent || '').trim())) { el.click(); return true; }
            }
            return false;
        }
        """
    )
    time.sleep(1.0)
    # Pick: click the exact "Round n" item.
    picked = h.page.evaluate(
        """
        (label) => {
            const els = Array.from(document.querySelectorAll('li, button, span, div, a'));
            for (const el of els) {
                if ((el.textContent || '').trim() === label) { el.click(); return true; }
            }
            return false;
        }
        """,
        f"Round {n}",
    )
    time.sleep(2.0)
    return bool(picked)


def collect_events(h: Harvester, rounds: range) -> list[dict]:
    index: dict[int, dict] = {}

    def absorb(round_no: int | None = None) -> int:
        added = 0
        for url, body in list(h.captured.items()):
            if f"season/{SEASON_ID}/events/round" not in url:
                continue
            try:
                feed = json.loads(body)
            except Exception:
                continue
            for e in feed.get("events", []):
                if e["id"] in index:
                    continue
                rinfo = (e.get("roundInfo") or {}).get("round")
                index[e["id"]] = {
                    "id": e["id"],
                    "customId": e.get("customId"),
                    "round": rinfo if rinfo is not None else round_no,
                    "startTimestamp": e.get("startTimestamp"),
                    "status": (e.get("status") or {}).get("type"),
                    "home": (e.get("homeTeam") or {}).get("name"),
                    "homeSlug": (e.get("homeTeam") or {}).get("slug"),
                    "homeId": (e.get("homeTeam") or {}).get("id"),
                    "away": (e.get("awayTeam") or {}).get("name"),
                    "awaySlug": (e.get("awayTeam") or {}).get("slug"),
                    "awayId": (e.get("awayTeam") or {}).get("id"),
                    "homeScore": (e.get("homeScore") or {}).get("current"),
                    "awayScore": (e.get("awayScore") or {}).get("current"),
                }
                added += 1
        return added

    print("\n[Phase A] collecting events round by round")
    absorb()  # whatever the matches tab already loaded (last round)
    for n in rounds:
        ok = select_round(h, n)
        # Give the round feed a moment, then absorb.
        for _ in range(6):
            if h.find(f"season/{SEASON_ID}/events/round/{n}"):
                break
            time.sleep(0.8)
        added = absorb(n)
        print(f"  round {n:>2}: selector={'ok' if ok else 'miss'} (+{added}, total {len(index)})")

    events = sorted(index.values(), key=lambda e: (e.get("round") or 0, e["id"]))
    EVENTS_INDEX.write_text(json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  saved events index -> {EVENTS_INDEX.name} ({len(events)} events)")
    return events


def event_dir(eid: int) -> Path:
    d = RAW / f"event_{eid}"
    d.mkdir(exist_ok=True)
    return d

def is_complete(eid: int) -> bool:
    d = RAW / f"event_{eid}"
    if not d.exists():
        return False
    return all((d / f"{part or 'event'}.json").exists() for part in EVENT_PARTS)

def scrape_event(h: Harvester, ev: dict) -> dict:
    eid = ev["id"]
    slug = f"{ev.get('homeSlug','home')}-{ev.get('awaySlug','away')}"
    custom = ev.get("customId") or ""
    url = f"https://www.sofascore.com/football/match/{slug}/{custom}#id:{eid}"

    h.captured.clear()
    h.visit(url, settle=3)

    # Each section fires only when its tab is active / scrolled into view.
    if h.click_text("Statistics"):
        h.harvest_until(f"event/{eid}/statistics", max_seconds=12)
    if h.click_text("Lineups"):
        h.harvest_until(f"event/{eid}/lineups", max_seconds=15)
    # shotmap is on the summary and is the laziest - go back and scroll for it.
    if not h.find(f"event/{eid}/shotmap"):
        h.click_text("Details")
        h.harvest_until(f"event/{eid}/shotmap", max_seconds=20)

    d = event_dir(eid)
    results = {}
    for part in EVENT_PARTS:
        suffix = f"/{part}" if part else ""
        data = h.find(f"event/{eid}{suffix}") if part else h.find(f"event/{eid}")
        # guard: event/{eid} substring also matches sub-resources; for the base
        # record require an exact match
        if not part:
            data = None
            for u, body in h.captured.items():
                if re.search(rf"/event/{eid}$", u):
                    data = json.loads(body)
                    break
        name = part or "event"
        if data is not None:
            (d / f"{name}.json").write_text(
                json.dumps(data, ensure_ascii=False), encoding="utf-8"
            )
            results[name] = True
        else:
            results[name] = False
    return results


def scrape_events(h: Harvester, events: list[dict], limit: int | None) -> None:
    pending = [e for e in events if e.get("status") == "finished" and not is_complete(e["id"])]
    if limit:
        pending = pending[:limit]
    total = len(pending)
    print(f"\n[Phase B] scraping {total} events "
          f"({sum(1 for e in events if is_complete(e['id']))} already complete)")

    PRIME_EVERY = 50      # proactive cookie refresh cadence
    start = time.time()
    consecutive_dead = 0

    for i, ev in enumerate(pending, 1):
        label = f"{ev.get('home')} {ev.get('homeScore')}-{ev.get('awayScore')} {ev.get('away')}"

        # Proactive refresh before Akamai starts throttling.
        if i > 1 and (i - 1) % PRIME_EVERY == 0:
            reprime(h)

        try:
            res = scrape_event(h, ev)
        except Exception as e:
            res = {}
            print(f"  [{i}/{total}] {label} -> ERROR {str(e)[:80]}")

        got_any = any(res.values()) if res else False
        # A fully-empty result means the session is blocked - reprime and retry.
        if not got_any:
            consecutive_dead += 1
            if consecutive_dead >= 1:
                reprime(h)
                consecutive_dead = 0
                try:
                    res = scrape_event(h, ev)
                except Exception as e:
                    res = {}
                    print(f"      retry ERROR {str(e)[:80]}")
        else:
            consecutive_dead = 0

        missing = [k for k, v in res.items() if not v] if res else ["ALL"]
        flag = "OK" if res and not missing else f"missing {missing}"
        elapsed = time.time() - start
        avg = elapsed / i
        eta_min = (total - i) * avg / 60
        print(f"  [{i}/{total}] R{ev.get('round')} {label} -> {flag} "
              f"| {avg:.0f}s/ev, ETA {eta_min:.0f} min")
        time.sleep(1.5)  # be polite


def parse_rounds(spec: str) -> range:
    m = re.match(r"^(\d+)-(\d+)$", spec)
    if m:
        return range(int(m.group(1)), int(m.group(2)) + 1)
    return range(int(spec), int(spec) + 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", default="1-34")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--events-only", action="store_true")
    ap.add_argument("--skip-collect", action="store_true")
    args = ap.parse_args()

    h = Harvester()
    try:
        prime(h)

        if args.skip_collect and EVENTS_INDEX.exists():
            events = json.loads(EVENTS_INDEX.read_text(encoding="utf-8"))
            print(f"reusing {EVENTS_INDEX.name} ({len(events)} events)")
        else:
            events = collect_events(h, parse_rounds(args.rounds))

        if args.events_only:
            print("\n--events-only set; stopping after Phase A")
            return

        scrape_events(h, events, args.limit)

        done = sum(1 for e in events if is_complete(e["id"]))
        print(f"\n=== done. {done}/{len(events)} events complete -> {RAW}")
    finally:
        h.close()


if __name__ == "__main__":
    main()
