"""Build a season-level player master table from the Sofascore data.

Combines per-player identity/attributes (read once from the raw lineups:
market value, date of birth, height, country, canonical position) with the
season aggregates derived from data/processed/sofascore_player_match.csv.

Writes data/processed/player_master.csv  (one row per player).
"""

import glob
import json
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw" / "sofascore"
PROC = ROOT / "data" / "processed"
SEASON_END = date(2026, 6, 1)  # reference point for age


def collect_identity() -> pd.DataFrame:
    """One pass over raw lineups -> latest known attributes per player."""
    rows = {}
    for d in sorted(glob.glob(str(RAW / "event_*"))):
        try:
            lu = json.loads((Path(d) / "lineups.json").read_text(encoding="utf-8"))
        except Exception:
            continue
        for side in ("home", "away"):
            for p in (lu.get(side) or {}).get("players", []):
                pl = p.get("player") or {}
                pid = pl.get("id")
                if not pid:
                    continue
                mv = (pl.get("proposedMarketValueRaw") or {}).get("value")
                country = (pl.get("country") or {}).get("name")
                rows[pid] = {  # last write wins = most recent match
                    "player_id": pid,
                    "name": pl.get("name"),
                    "slug": pl.get("slug"),
                    "canonical_position": pl.get("position"),
                    "market_value_eur": mv,
                    "height_cm": pl.get("height"),
                    "country": country,
                    "dob_ts": pl.get("dateOfBirthTimestamp"),
                }
    df = pd.DataFrame(rows.values())
    df["dob"] = df["dob_ts"].apply(
        lambda t: datetime.fromtimestamp(t, tz=timezone.utc).date().isoformat() if pd.notna(t) else None
    )
    df["age"] = df["dob_ts"].apply(_age)
    return df.drop(columns=["dob_ts"])


def _age(ts):
    if pd.isna(ts):
        return None
    b = datetime.fromtimestamp(ts, tz=timezone.utc).date()
    return SEASON_END.year - b.year - ((SEASON_END.month, SEASON_END.day) < (b.month, b.day))


def aggregate_stats() -> pd.DataFrame:
    pm = pd.read_csv(PROC / "sofascore_player_match.csv")
    num = pm.select_dtypes("number").columns

    # sums of counting stats
    sum_cols = [c for c in num if c not in ("match_id", "round", "team_id", "player_id", "rating")]
    g = pm.groupby("player_id")
    agg = g[sum_cols].sum(min_count=1)

    # appearances, minutes-weighted rating, dominant team + position
    agg["appearances"] = g["match_id"].nunique()
    agg["starts"] = pm.assign(start=~pm["substitute"].fillna(False)).groupby("player_id")["start"].sum()
    agg["avg_rating"] = _weighted_rating(pm)
    agg["team"] = _mode_by_minutes(pm, "team")
    agg["lineup_position"] = _mode_by_minutes(pm, "position")
    return agg.reset_index()


def _weighted_rating(pm: pd.DataFrame) -> pd.Series:
    d = pm.dropna(subset=["rating"]).copy()
    d["w"] = d["minutesPlayed"].fillna(0).clip(lower=1)
    wr = d.groupby("player_id").apply(
        lambda x: np.average(x["rating"], weights=x["w"]), include_groups=False
    )
    return wr


def _mode_by_minutes(pm: pd.DataFrame, col: str) -> pd.Series:
    d = pm.groupby(["player_id", col])["minutesPlayed"].sum().reset_index()
    idx = d.groupby("player_id")["minutesPlayed"].idxmax()
    return d.loc[idx].set_index("player_id")[col]


def main() -> None:
    ident = collect_identity()
    stats = aggregate_stats()
    df = ident.merge(stats, on="player_id", how="right")

    mins = df["minutesPlayed"].replace(0, np.nan)
    per90 = {
        "goals_p90": "goals",
        "xg_p90": "expectedGoals",
        "xa_p90": "expectedAssists",
        "shots_p90": "totalShots",
        "key_passes_p90": "keyPass",
        "prog_carries_p90": "progressiveBallCarriesCount",
        "tackles_p90": "totalTackle",
        "interceptions_p90": "interceptionWon",
        "recoveries_p90": "ballRecovery",
    }
    for new, src in per90.items():
        if src in df.columns:
            df[new] = (df[src] / mins * 90).round(3)

    df = df.rename(columns={"minutesPlayed": "minutes", "expectedGoals": "xg",
                            "expectedAssists": "xa", "goalAssist": "assists"})

    front = ["player_id", "name", "team", "canonical_position", "lineup_position",
             "age", "dob", "height_cm", "country", "market_value_eur",
             "appearances", "starts", "minutes", "avg_rating",
             "goals", "assists", "xg", "xa"]
    cols = front + [c for c in df.columns if c not in front]
    df = df[cols].sort_values("minutes", ascending=False)

    out = PROC / "player_master.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"player_master.csv  {df.shape[0]} players x {df.shape[1]} cols -> {out}")
    print("\ntop 10 by market value:")
    top = df.sort_values("market_value_eur", ascending=False).head(10)
    print(top[["name", "team", "age", "market_value_eur", "minutes", "xg", "avg_rating"]].to_string(index=False))


if __name__ == "__main__":
    main()
