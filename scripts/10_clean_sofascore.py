"""Flatten the raw Sofascore JSON (scripts/09 output) into analysis CSVs.

Reads:
    data/raw/sofascore/events_index.json
    data/raw/sofascore/event_{id}/{event,shotmap,statistics,lineups,incidents}.json

Writes (data/processed/):
    sofascore_matches.csv        one row per match  (team xG, possession, shots, passes, ...)
    sofascore_shots.csv          one row per shot   (xg, xgot, location, body part, situation)
    sofascore_player_match.csv   one row per player per match (rating, xG, xA, touches, duels, ...)

Only finished matches with the full set of files are included. Run scripts/09
again first if events_index.json reports missing parts.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent.parent / "data" / "raw" / "sofascore"
OUT = Path(__file__).parent.parent / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)
EVENTS_INDEX = RAW / "events_index.json"


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def to_date(ts):
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()


# Team-level stats we keep, mapped to a short column slug.
TEAM_STAT_COLS = {
    "Expected goals": "xg",
    "Ball possession": "possession",
    "Total shots": "shots",
    "Shots on target": "shots_on_target",
    "Big chances": "big_chances",
    "Big chances missed": "big_chances_missed",
    "Corner kicks": "corners",
    "Passes": "passes",
    "Accurate passes": "accurate_passes",
    "Fouls": "fouls",
    "Tackles": "tackles",
    "Interceptions": "interceptions",
    "Recoveries": "recoveries",
    "Touches in penalty area": "touches_in_box",
    "Final third entries": "final_third_entries",
    "Yellow cards": "yellow_cards",
    "Goalkeeper saves": "gk_saves",
    "Goals prevented": "goals_prevented",
}

# Per-player stat keys we keep (numeric). Missing keys default to 0/NaN.
PLAYER_STAT_KEYS = [
    "minutesPlayed", "rating",
    "expectedGoals", "expectedAssists", "goals", "goalAssist",
    "totalShots", "shotOffTarget", "onTargetScoringAttempt",
    "touches", "totalPass", "accuratePass", "keyPass",
    "totalLongBalls", "accurateLongBalls",
    "totalCross", "accurateCross",
    "duelWon", "duelLost", "aerialWon", "aerialLost",
    "totalTackle", "wonTackle", "interceptionWon", "totalClearance",
    "ballRecovery", "possessionLostCtrl", "fouls", "wasFouled",
    "dribbleValueNormalized", "totalProgression", "progressiveBallCarriesCount",
    "saves", "goalsPrevented",
]


def stat_map(statistics_json) -> dict:
    """Return {stat_name: (homeValue, awayValue)} for the ALL period, preferring
    numeric *Value fields and falling back to parsing the display strings."""
    out = {}
    if not statistics_json:
        return out
    for grp in statistics_json.get("statistics", []):
        if grp.get("period") != "ALL":
            continue
        for sub in grp.get("groups", []):
            for it in sub.get("statisticsItems", []):
                name = it.get("name")
                hv, av = it.get("homeValue"), it.get("awayValue")
                if hv is None:
                    hv = _num(it.get("home"))
                if av is None:
                    av = _num(it.get("away"))
                out[name] = (hv, av)
    return out


def _num(s):
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return s
    s = str(s).strip().replace("%", "")
    # forms like "105/136 (77)" -> take the leading number
    s = s.split("/")[0].split("(")[0].strip()
    try:
        return float(s)
    except ValueError:
        return None


def build_matches(events) -> pd.DataFrame:
    rows = []
    for ev in events:
        eid = ev["id"]
        d = RAW / f"event_{eid}"
        meta = load(d / "event.json")
        meta = (meta or {}).get("event", meta) if meta else {}
        sm = stat_map(load(d / "statistics.json"))

        row = {
            "match_id": eid,
            "round": ev.get("round"),
            "date": to_date(ev.get("startTimestamp")),
            "home_team": ev.get("home"),
            "home_id": ev.get("homeId"),
            "away_team": ev.get("away"),
            "away_id": ev.get("awayId"),
            "home_score": ev.get("homeScore"),
            "away_score": ev.get("awayScore"),
            "venue": ((meta.get("venue") or {}).get("stadium") or {}).get("name")
                     if isinstance(meta.get("venue"), dict) else None,
            "city": ((meta.get("venue") or {}).get("city") or {}).get("name")
                    if isinstance(meta.get("venue"), dict) else None,
            "referee": (meta.get("referee") or {}).get("name"),
        }
        hs, as_ = ev.get("homeScore"), ev.get("awayScore")
        row["result"] = ("H" if hs > as_ else "A" if as_ > hs else "D") if (hs is not None and as_ is not None) else None

        for stat_name, slug in TEAM_STAT_COLS.items():
            hv, av = sm.get(stat_name, (None, None))
            row[f"home_{slug}"] = hv
            row[f"away_{slug}"] = av

        rows.append(row)
    return pd.DataFrame(rows)


def build_shots(events) -> pd.DataFrame:
    rows = []
    for ev in events:
        eid = ev["id"]
        sm = load(RAW / f"event_{eid}" / "shotmap.json")
        shots = (sm or {}).get("shotmap") or (sm or {}).get("shots") or []
        for s in shots:
            pc = s.get("playerCoordinates") or {}
            gm = s.get("goalMouthCoordinates") or {}
            player = s.get("player") or {}
            is_home = s.get("isHome")
            rows.append({
                "match_id": eid,
                "round": ev.get("round"),
                "team": ev.get("home") if is_home else ev.get("away"),
                "is_home": is_home,
                "player": player.get("name"),
                "player_id": player.get("id"),
                "minute": s.get("time"),
                "shot_type": s.get("shotType"),
                "is_goal": s.get("shotType") == "goal",
                "situation": s.get("situation"),
                "body_part": s.get("bodyPart"),
                "xg": s.get("xg"),
                "xgot": s.get("xgot"),
                "x": pc.get("x"),
                "y": pc.get("y"),
                "goal_mouth_y": gm.get("y"),
                "goal_mouth_z": gm.get("z"),
            })
    return pd.DataFrame(rows)


def build_player_match(events) -> pd.DataFrame:
    rows = []
    for ev in events:
        eid = ev["id"]
        lu = load(RAW / f"event_{eid}" / "lineups.json")
        if not lu:
            continue
        for side, is_home in (("home", True), ("away", False)):
            team_name = ev.get("home") if is_home else ev.get("away")
            team_id = ev.get("homeId") if is_home else ev.get("awayId")
            for p in (lu.get(side) or {}).get("players", []):
                player = p.get("player") or {}
                st = p.get("statistics") or {}
                if not st:
                    continue  # unused sub, no stats
                row = {
                    "match_id": eid,
                    "round": ev.get("round"),
                    "team": team_name,
                    "team_id": team_id,
                    "is_home": is_home,
                    "player": player.get("name"),
                    "player_id": player.get("id"),
                    "position": p.get("position"),
                    "substitute": p.get("substitute"),
                }
                for k in PLAYER_STAT_KEYS:
                    row[k] = st.get(k)
                rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    events = json.loads(EVENTS_INDEX.read_text(encoding="utf-8"))
    finished = [e for e in events if e.get("status") == "finished"]
    # keep only those with all five files present
    ready = []
    for e in finished:
        d = RAW / f"event_{e['id']}"
        if all((d / f"{p}.json").exists() for p in ("event", "shotmap", "statistics", "lineups", "incidents")):
            ready.append(e)
    print(f"{len(ready)}/{len(finished)} finished matches have complete raw data")

    matches = build_matches(ready)
    shots = build_shots(ready)
    players = build_player_match(ready)

    matches.to_csv(OUT / "sofascore_matches.csv", index=False, encoding="utf-8-sig")
    shots.to_csv(OUT / "sofascore_shots.csv", index=False, encoding="utf-8-sig")
    players.to_csv(OUT / "sofascore_player_match.csv", index=False, encoding="utf-8-sig")

    print(f"  sofascore_matches.csv       {matches.shape[0]:>5} rows x {matches.shape[1]} cols")
    print(f"  sofascore_shots.csv         {shots.shape[0]:>5} rows x {shots.shape[1]} cols")
    print(f"  sofascore_player_match.csv  {players.shape[0]:>5} rows x {players.shape[1]} cols")
    print(f"\nwritten to {OUT}")


if __name__ == "__main__":
    main()
