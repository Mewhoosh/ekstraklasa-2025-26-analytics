"""Export clean wide tables for the Power BI dashboard.

Power Query in Power BI Desktop can do this work but it is awkward for a
junior BI user. I do the heavy joins in pandas and write five flat CSVs
ready to drop into Power BI as separate tables.

Outputs (data/processed/powerbi/):
    team_match_long.csv   one row per team per match (612 rows)
    season_team.csv       one row per team (18 rows)
    players.csv           one row per player (player_master + per-90 columns)
    matches.csv           one row per match (cross-reference for drill-through)
    shots.csv             one row per shot (with team and player names)
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import poisson


REPO = Path(__file__).resolve().parent.parent
SOFA = REPO / "data" / "processed" / "sofascore"
OUT = REPO / "data" / "processed" / "powerbi"
OUT.mkdir(parents=True, exist_ok=True)


def build_team_match_long(matches: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "match_id", "round", "date", "team", "opp", "gf", "ga", "xg", "xga",
        "possession", "shots", "opp_shots", "sot", "big_chances", "corners",
        "passes", "acc_passes", "touches_in_box", "final_third_entries",
        "recoveries", "goals_prevented",
    ]
    home = matches.rename(columns={
        "home_team": "team", "away_team": "opp",
        "home_score": "gf", "away_score": "ga",
        "home_xg": "xg", "away_xg": "xga",
        "home_possession": "possession",
        "home_shots": "shots", "away_shots": "opp_shots",
        "home_shots_on_target": "sot",
        "home_big_chances": "big_chances",
        "home_corners": "corners",
        "home_passes": "passes", "home_accurate_passes": "acc_passes",
        "home_touches_in_box": "touches_in_box",
        "home_final_third_entries": "final_third_entries",
        "home_recoveries": "recoveries",
        "home_goals_prevented": "goals_prevented",
    })[cols].assign(venue="H")
    away = matches.rename(columns={
        "away_team": "team", "home_team": "opp",
        "away_score": "gf", "home_score": "ga",
        "away_xg": "xg", "home_xg": "xga",
        "away_possession": "possession",
        "away_shots": "shots", "home_shots": "opp_shots",
        "away_shots_on_target": "sot",
        "away_big_chances": "big_chances",
        "away_corners": "corners",
        "away_passes": "passes", "away_accurate_passes": "acc_passes",
        "away_touches_in_box": "touches_in_box",
        "away_final_third_entries": "final_third_entries",
        "away_recoveries": "recoveries",
        "away_goals_prevented": "goals_prevented",
    })[cols].assign(venue="A")
    long = (pd.concat([home, away], ignore_index=True)
              .sort_values(["date", "match_id"])
              .reset_index(drop=True))
    long["result"] = np.where(long["gf"] > long["ga"], "W",
                       np.where(long["gf"] < long["ga"], "L", "D"))
    long["pts"] = long["result"].map({"W": 3, "D": 1, "L": 0})

    MAX_GOALS = 8
    def xpts_row(row):
        p_for = poisson.pmf(np.arange(MAX_GOALS + 1), row["xg"])
        p_against = poisson.pmf(np.arange(MAX_GOALS + 1), row["xga"])
        joint = np.outer(p_for, p_against)
        p_win = np.tril(joint, -1).sum()
        p_draw = np.trace(joint)
        p_loss = np.triu(joint, 1).sum()
        return pd.Series({"xpts": 3 * p_win + 1 * p_draw,
                          "p_win": p_win, "p_draw": p_draw, "p_loss": p_loss})

    xp = long.apply(xpts_row, axis=1)
    long = pd.concat([long, xp], axis=1)

    long["phase"] = np.where(long["round"] <= 17, "Autumn", "Spring")
    return long


def _h2h_standings(tm_long: pd.DataFrame) -> pd.DataFrame:
    """Standings with Ekstraklasa tie-breaks: pts, H2H pts, H2H GD, overall GD, GF."""
    base = tm_long.groupby("team", as_index=False).agg(
        pts=("pts", "sum"), gf=("gf", "sum"), ga=("ga", "sum"),
    )
    base["gd"] = base["gf"] - base["ga"]
    rows = []
    for pts_val in sorted(base["pts"].unique(), reverse=True):
        group = base[base["pts"] == pts_val].copy()
        if len(group) == 1:
            rows.append(group)
            continue
        teams = group["team"].tolist()
        h2h = tm_long[tm_long["team"].isin(teams) & tm_long["opp"].isin(teams)]
        h2h_pts = h2h.groupby("team")["pts"].sum().reindex(teams, fill_value=0)
        h2h_gf = h2h.groupby("team")["gf"].sum().reindex(teams, fill_value=0)
        h2h_ga = h2h.groupby("team")["ga"].sum().reindex(teams, fill_value=0)
        group["_h2h_pts"] = group["team"].map(h2h_pts)
        group["_h2h_gd"] = group["team"].map(h2h_gf - h2h_ga)
        group = group.sort_values(
            ["_h2h_pts", "_h2h_gd", "gd", "gf"],
            ascending=[False, False, False, False],
        ).drop(columns=["_h2h_pts", "_h2h_gd"])
        rows.append(group)
    out = pd.concat(rows, ignore_index=True)
    out["pos"] = out.index + 1
    return out[["team", "pos"]]


def build_season_team(tm_long: pd.DataFrame) -> pd.DataFrame:
    season = tm_long.groupby("team", as_index=False).agg(
        mp=("match_id", "count"),
        wins=("result", lambda s: (s == "W").sum()),
        draws=("result", lambda s: (s == "D").sum()),
        losses=("result", lambda s: (s == "L").sum()),
        pts=("pts", "sum"),
        xpts=("xpts", "sum"),
        gf=("gf", "sum"),
        ga=("ga", "sum"),
        xg=("xg", "sum"),
        xga=("xga", "sum"),
        goals_prevented=("goals_prevented", "sum"),
    )
    season["pts_diff"] = season["pts"] - season["xpts"]
    season["gd"] = season["gf"] - season["ga"]
    season["xgd"] = season["xg"] - season["xga"]
    season["finishing"] = season["gf"] - season["xg"]
    season["defending"] = season["xga"] - season["ga"]

    pos_table = _h2h_standings(tm_long)
    season = season.merge(pos_table, on="team")

    xpos = season.sort_values("xpts", ascending=False).reset_index(drop=True)
    xpos["xpos"] = xpos.index + 1
    season = season.merge(xpos[["team", "xpos"]], on="team")
    season["pos_swing"] = season["xpos"] - season["pos"]
    season = season.sort_values("pos").reset_index(drop=True)
    return season


def build_players() -> pd.DataFrame:
    p = pd.read_csv(SOFA / "player_master.csv")

    def role(pos):
        if pd.isna(pos):
            return None
        s = str(pos).upper()
        if s.startswith("G"): return "GK"
        if s.startswith("D"): return "DEF"
        if s.startswith("M"): return "MID"
        if s.startswith("F") or s.startswith("S") or s.startswith("A"): return "FWD"
        return "MID"

    p["role"] = p["canonical_position"].apply(role)
    p["ga_total"] = p["goals"].fillna(0) + p.get("assists", 0).fillna(0)
    p["xga_total"] = p["xg"].fillna(0) + p["xa"].fillna(0)
    p["mv_millions"] = p["market_value_eur"].fillna(0) / 1_000_000
    return p


def _clean_numerics(df: pd.DataFrame) -> pd.DataFrame:
    """Power BI auto-detects numeric column types from the first rows. If a
    later row has an empty value it refuses to convert the whole column to
    Decimal. Replace numeric NaN with 0 so import is friction-free.
    """
    out = df.copy()
    for col in out.select_dtypes(include=[np.number]).columns:
        out[col] = out[col].fillna(0)
    return out


def main() -> None:
    matches = pd.read_csv(SOFA / "sofascore_matches.csv")
    matches["date"] = pd.to_datetime(matches["date"])
    shots = pd.read_csv(SOFA / "sofascore_shots.csv")

    tm_long = build_team_match_long(matches)
    season = build_season_team(tm_long)
    players = build_players()

    _clean_numerics(tm_long).to_csv(OUT / "team_match_long.csv", index=False)
    _clean_numerics(season).to_csv(OUT / "season_team.csv", index=False)
    _clean_numerics(players).to_csv(OUT / "players.csv", index=False)
    _clean_numerics(matches).to_csv(OUT / "matches.csv", index=False)
    _clean_numerics(shots).to_csv(OUT / "shots.csv", index=False)

    print("Wrote:")
    for name in ["team_match_long.csv", "season_team.csv",
                 "players.csv", "matches.csv", "shots.csv"]:
        rows = pd.read_csv(OUT / name).shape[0]
        print(f"  {name:<25} {rows} rows")
    print(f"\nOutput dir: {OUT}")


if __name__ == "__main__":
    main()
