"""Shared loaders, palette and helpers for the Streamlit app.

All pages import from here. Caching avoids re-reading the CSVs on every
widget interaction.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import poisson


REPO_ROOT = Path(__file__).resolve().parent.parent
SOFA_DIR = REPO_ROOT / "data" / "processed" / "sofascore"
FBREF_DIR = REPO_ROOT / "data" / "processed" / "fbref"

JAGA = "crimson"
LECH = "royalblue"
LEGIA = "forestgreen"
GREY = "#9aa0a6"

FOCUS_COLORS = {
    "Jagiellonia Białystok": JAGA,
    "Lech Poznań": LECH,
    "Legia Warszawa": LEGIA,
}

TEAM_COLORS = {
    "Jagiellonia Białystok": JAGA,
    "Lech Poznań": LECH,
    "Legia Warszawa": LEGIA,
    "Raków Częstochowa": "#b91c1c",
    "Pogoń Szczecin": "#0f766e",
    "KS Lechia Gdańsk": "#16a34a",
    "Górnik Zabrze": "#7c3aed",
    "Wisła Płock": "#1e3a8a",
    "Cracovia": "#dc2626",
    "Motor Lublin": "#ca8a04",
    "GKS Katowice": "#facc15",
    "MKS Korona Kielce": "#ea580c",
    "Bruk-Bet Termalica Nieciecza": "#15803d",
    "Widzew Łódź": "#991b1b",
    "Piast Gliwice": "#0891b2",
    "MZKS Arka Gdynia": "#fbbf24",
    "Radomiak Radom": "#10b981",
    "Zagłębie Lubin": "#b45309",
}


@st.cache_data
def load_matches() -> pd.DataFrame:
    df = pd.read_csv(SOFA_DIR / "sofascore_matches.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_shots() -> pd.DataFrame:
    return pd.read_csv(SOFA_DIR / "sofascore_shots.csv")


@st.cache_data
def load_player_match() -> pd.DataFrame:
    return pd.read_csv(SOFA_DIR / "sofascore_player_match.csv")


@st.cache_data
def load_players() -> pd.DataFrame:
    df = pd.read_csv(SOFA_DIR / "player_master.csv")
    df["role"] = df["canonical_position"].apply(_role)
    return df


@st.cache_data
def load_standings() -> pd.DataFrame:
    return pd.read_csv(FBREF_DIR / "league_standings.csv")


def _role(pos):
    if pos is None or (isinstance(pos, float) and np.isnan(pos)):
        return None
    p = str(pos).upper()
    if p.startswith("G"):
        return "GK"
    if p.startswith("D"):
        return "DEF"
    if p.startswith("M"):
        return "MID"
    if p.startswith("F") or p.startswith("S") or p.startswith("A"):
        return "FWD"
    return "MID"


@st.cache_data
def team_match_long() -> pd.DataFrame:
    """One row per team per match (2 rows per match). Used by every team-level
    page so it lives here, cached once."""
    m = load_matches()
    cols = [
        "match_id", "round", "date", "team", "opp", "gf", "ga", "xg", "xga",
        "possession", "shots", "opp_shots", "sot", "big_chances", "corners",
        "passes", "acc_passes", "touches_in_box", "final_third_entries",
        "recoveries", "goals_prevented",
    ]
    home = m.rename(columns={
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
    away = m.rename(columns={
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
    long = pd.concat([home, away], ignore_index=True).sort_values(["date", "match_id"])
    long["result"] = np.where(long["gf"] > long["ga"], "W",
                       np.where(long["gf"] < long["ga"], "L", "D"))
    long["pts"] = long["result"].map({"W": 3, "D": 1, "L": 0})
    long = long.reset_index(drop=True)

    xp = long.apply(lambda r: _xpts(r["xg"], r["xga"]), axis=1, result_type="expand")
    xp.columns = ["xpts", "p_win", "p_draw", "p_loss"]
    long = pd.concat([long, xp], axis=1)
    return long


MAX_GOALS = 8


def _xpts(xg_for, xg_against):
    p_for = poisson.pmf(np.arange(MAX_GOALS + 1), xg_for)
    p_against = poisson.pmf(np.arange(MAX_GOALS + 1), xg_against)
    joint = np.outer(p_for, p_against)
    p_win = np.tril(joint, -1).sum()
    p_draw = np.trace(joint)
    p_loss = np.triu(joint, 1).sum()
    return 3 * p_win + 1 * p_draw, p_win, p_draw, p_loss


def xpts_for(xg_for: float, xg_against: float) -> dict:
    xpts, p_win, p_draw, p_loss = _xpts(xg_for, xg_against)
    return {"xpts": xpts, "p_win": p_win, "p_draw": p_draw, "p_loss": p_loss}


def color_for(team: str) -> str:
    return TEAM_COLORS.get(team, "#5a6470")


def standings_at(team_match_df: pd.DataFrame, round_n: int) -> pd.DataFrame:
    """Standings after round_n with Ekstraklasa tie-breaks:
    1. Points
    2. Head-to-head points
    3. Head-to-head goal difference
    4. Overall goal difference
    5. Goals scored
    """
    sub = team_match_df[team_match_df["round"] <= round_n].copy()
    base = sub.groupby("team", as_index=False).agg(
        pts=("pts", "sum"), gf=("gf", "sum"), ga=("ga", "sum"),
    )
    base["gd"] = base["gf"] - base["ga"]

    result_rows = []
    for pts_val in sorted(base["pts"].unique(), reverse=True):
        group = base[base["pts"] == pts_val].copy()
        if len(group) == 1:
            result_rows.append(group)
            continue
        teams = group["team"].tolist()
        h2h = sub[sub["team"].isin(teams) & sub["opp"].isin(teams)]
        h2h_pts = h2h.groupby("team")["pts"].sum().reindex(teams, fill_value=0)
        h2h_gf = h2h.groupby("team")["gf"].sum().reindex(teams, fill_value=0)
        h2h_ga = h2h.groupby("team")["ga"].sum().reindex(teams, fill_value=0)
        group["_h2h_pts"] = group["team"].map(h2h_pts)
        group["_h2h_gd"] = group["team"].map(h2h_gf - h2h_ga)
        group = group.sort_values(
            ["_h2h_pts", "_h2h_gd", "gd", "gf"],
            ascending=[False, False, False, False],
        )
        result_rows.append(group.drop(columns=["_h2h_pts", "_h2h_gd"]))

    final = pd.concat(result_rows, ignore_index=True)
    final["pos"] = final.index + 1
    return final


def add_pitch_shapes(fig: go.Figure) -> go.Figure:
    """Draw a vertical half-pitch on a plotly Figure. Goal at top (y=52.5),
    halfway line at bottom (y=0)."""
    line = dict(color="#888", width=1.5)
    shapes = [
        dict(type="line", x0=0, y0=0, x1=68, y1=0, line=line),
        dict(type="line", x0=0, y0=52.5, x1=68, y1=52.5, line=line),
        dict(type="line", x0=0, y0=0, x1=0, y1=52.5, line=line),
        dict(type="line", x0=68, y0=0, x1=68, y1=52.5, line=line),
        dict(type="line", x0=13.84, y0=36, x1=54.16, y1=36, line=line),
        dict(type="line", x0=13.84, y0=36, x1=13.84, y1=52.5, line=line),
        dict(type="line", x0=54.16, y0=36, x1=54.16, y1=52.5, line=line),
        dict(type="line", x0=24.84, y0=47, x1=43.16, y1=47, line=line),
        dict(type="line", x0=24.84, y0=47, x1=24.84, y1=52.5, line=line),
        dict(type="line", x0=43.16, y0=47, x1=43.16, y1=52.5, line=line),
        dict(type="line", x0=30.34, y0=52.5, x1=37.66, y1=52.5,
             line=dict(color="#222", width=4)),
    ]
    fig.update_layout(shapes=shapes)
    return fig


def shot_map_figure(shots_df: pd.DataFrame, color: str, title: str = "") -> go.Figure:
    """Vertical half-pitch shot map. Shots near opp goal land at top of plot."""
    fig = go.Figure()
    s = shots_df.dropna(subset=["x", "y", "xg"]).copy()
    s["pitch_x"] = s["y"] * 0.68
    s["pitch_y"] = (50 - s["x"]) * 1.05
    goals = s[s["is_goal"]]
    misses = s[~s["is_goal"]]
    fig.add_trace(go.Scatter(
        x=misses["pitch_x"], y=misses["pitch_y"], mode="markers",
        marker=dict(size=misses["xg"] * 25 + 4, color="rgba(0,0,0,0)",
                    line=dict(color="#5a6470", width=1)),
        name="non-goal", hovertext=misses.get("player", ""),
        hoverinfo="text",
    ))
    fig.add_trace(go.Scatter(
        x=goals["pitch_x"], y=goals["pitch_y"], mode="markers",
        marker=dict(size=goals["xg"] * 25 + 6, color=color,
                    line=dict(color="white", width=1.5)),
        name="goal", hovertext=goals.get("player", ""),
        hoverinfo="text",
    ))
    add_pitch_shapes(fig)
    fig.update_layout(
        title=title,
        xaxis=dict(range=[-2, 70], visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(range=[-2, 55], visible=False),
        height=550,
        showlegend=False,
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def pizza_figure(player_row: pd.Series, pool_df: pd.DataFrame,
                 metrics: dict, color: str, title: str = "") -> go.Figure:
    """Polar bar pizza chart of percentile ranks vs pool."""
    labels = list(metrics.keys())
    pcts = [(pool_df[c] < player_row[c]).mean() * 100 for c in metrics.values()]
    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        r=pcts, theta=labels, marker_color=color,
        marker_line_color="white", marker_line_width=2,
        opacity=0.85, hovertext=[f"{p:.0f}" for p in pcts], hoverinfo="text+theta",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[110] * len(labels), theta=labels, mode="text",
        text=[f"{p:.0f}" for p in pcts],
        textfont=dict(size=12, color=color),
        showlegend=False, hoverinfo="skip",
    ))
    fig.update_layout(
        title=title,
        polar=dict(
            radialaxis=dict(range=[0, 115], showticklabels=False, ticks=""),
            angularaxis=dict(direction="clockwise", rotation=90),
        ),
        height=520,
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=False,
    )
    return fig
