"""Player explorer - filter by anything, pick a row, see pizza + shot map."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import (
    load_players, load_shots, load_player_match, load_matches,
    color_for, JAGA, shot_map_figure, pizza_figure,
)


st.set_page_config(page_title="Player Explorer", layout="wide")

players = load_players()
shots = load_shots()
player_match = load_player_match()
matches = load_matches()

st.title("Player explorer")
st.caption("Filter the player pool, pick a row, see the pizza and shot map.")

teams = sorted(players["team"].dropna().unique())
roles = ["FWD", "MID", "DEF", "GK"]

c1, c2, c3, c4 = st.columns(4)
sel_teams = c1.multiselect("Teams", teams, default=teams)
sel_roles = c2.multiselect("Roles", roles, default=roles)
min_minutes = c3.slider("Min minutes", 0, int(players["minutes"].max()), 900, step=100)
max_age = c4.slider("Max age", 16, 45, 35)

mv_max_eur = int(players["market_value_eur"].dropna().max())
max_mv = st.slider("Max market value (EUR)", 0, mv_max_eur,
                   mv_max_eur, step=100_000)

filtered = players[
    players["team"].isin(sel_teams)
    & players["role"].isin(sel_roles)
    & (players["minutes"] >= min_minutes)
    & (players["age"] <= max_age)
    & (players["market_value_eur"].fillna(0) <= max_mv)
].copy()

st.markdown(f"**{len(filtered)} players** match the filters.")

cols = ["name", "team", "role", "age", "minutes", "market_value_eur",
        "goals", "xg", "xa", "avg_rating"]
show = filtered[cols].copy()
show["minutes"] = show["minutes"].fillna(0).astype(int)
show["goals"] = show["goals"].fillna(0).astype(int)
show["market_value_eur"] = show["market_value_eur"].fillna(0).astype(int)
show["xg"] = show["xg"].round(1)
show["xa"] = show["xa"].round(2)
show["avg_rating"] = show["avg_rating"].round(2)
show = show.rename(columns={
    "name": "Name", "team": "Team", "role": "Role", "age": "Age",
    "minutes": "Min", "market_value_eur": "MV (EUR)",
    "goals": "G", "xg": "xG", "xa": "xA", "avg_rating": "Rating",
})

st.dataframe(show, use_container_width=True, hide_index=True, height=380)

st.subheader("Player spotlight")
if filtered.empty:
    st.info("No players match the filters - relax them.")
    st.stop()

_names = filtered["name"].tolist()
_default = _names.index("Bartosz Nowak") if "Bartosz Nowak" in _names else 0
sel_player = st.selectbox("Player", _names, index=_default)
player_row = filtered[filtered["name"] == sel_player].iloc[0]
color = color_for(player_row["team"])

def _safe_int(v):
    return int(v) if pd.notna(v) else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Team", player_row["team"])
c2.metric("Minutes", _safe_int(player_row["minutes"]))
c3.metric("MV (EUR)", f"{_safe_int(player_row['market_value_eur']):,}")
c4.metric("Goals", _safe_int(player_row.get("goals")))

if player_row["role"] == "GK":
    GK_PIZZA = {
        "GP/90":     "_gp_p90",
        "Saves/90":  "_saves_p90",
        "Pass acc":  "_pass_acc",
        "LB acc":    "_lb_acc",
        "LB/90":     "_lb_p90",
        "Recov/90":  "_recov_p90",
    }
    gk_pool = players[(players["role"] == "GK") & (players["minutes"] >= 900)].copy()
    gk_pool["_gp_p90"]    = gk_pool["goalsPrevented"] / gk_pool["minutes"] * 90
    gk_pool["_saves_p90"] = gk_pool["saves"] / gk_pool["minutes"] * 90
    gk_pool["_pass_acc"]  = gk_pool["accuratePass"] / gk_pool["totalPass"].replace(0, np.nan) * 100
    gk_pool["_lb_acc"]    = gk_pool["accurateLongBalls"] / gk_pool["totalLongBalls"].replace(0, np.nan) * 100
    gk_pool["_lb_p90"]    = gk_pool["totalLongBalls"] / gk_pool["minutes"] * 90
    gk_pool["_recov_p90"] = gk_pool["ballRecovery"] / gk_pool["minutes"] * 90
    for c in GK_PIZZA.values():
        gk_pool[c] = gk_pool[c].fillna(0)
    if player_row["player_id"] in gk_pool["player_id"].values:
        row = gk_pool[gk_pool["player_id"] == player_row["player_id"]].iloc[0]
        fig = pizza_figure(row, gk_pool, GK_PIZZA, color,
                           f"{sel_player} - GK percentile")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pizza needs 900+ minutes for percentile baseline.")
else:
    ATTACK_PIZZA = {
        "Goals":      "goals_p90",
        "xG":         "xg_p90",
        "xA":         "xa_p90",
        "Shots":      "shots_p90",
        "Key passes": "key_passes_p90",
        "Carries":    "prog_carries_p90",
        "Aerials":    "_aerials_p90",
        "Recoveries": "recoveries_p90",
    }
    pool = players[
        players["role"].isin(["FWD", "MID"]) & (players["minutes"] >= 900)
    ].copy()
    pool["_aerials_p90"] = pool["aerialWon"] / pool["minutes"] * 90
    for c in ATTACK_PIZZA.values():
        pool[c] = pool[c].fillna(0)
    if player_row["player_id"] in pool["player_id"].values:
        row = pool[pool["player_id"] == player_row["player_id"]].iloc[0]
        fig = pizza_figure(row, pool, ATTACK_PIZZA, color,
                           f"{sel_player} - attacker percentile")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pizza needs 900+ minutes for percentile baseline.")

player_shots = shots[shots["player"] == sel_player]
if not player_shots.empty:
    fig = shot_map_figure(player_shots, color, f"{sel_player} - shot map")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"{len(player_shots)} shots, {int(player_shots['is_goal'].sum())} goals, "
               f"xG total {player_shots['xg'].sum():.1f}")

st.subheader("Match by match")
pm = player_match[player_match["player_id"] == player_row["player_id"]].sort_values("round").copy()
opp_lookup = matches.set_index("match_id")[["home_team", "away_team"]]
pm = pm.merge(opp_lookup, on="match_id", how="left")
pm["opponent"] = np.where(pm["is_home"], pm["away_team"], pm["home_team"])
pm["venue"] = np.where(pm["is_home"], "H", "A")
if pm.empty:
    st.info("No per-match records for this player.")
else:
    if player_row["role"] == "GK":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=pm["round"], y=pm["rating"], mode="lines+markers",
                                 name="Rating", line=dict(color=color, width=2)))
        fig.add_trace(go.Bar(x=pm["round"], y=pm["goalsPrevented"],
                             name="Goals prevented", marker_color=color, opacity=0.3,
                             yaxis="y2"))
        fig.update_layout(
            xaxis_title="Matchweek",
            yaxis=dict(title="Sofascore rating", range=[5, 10]),
            yaxis2=dict(title="Goals prevented", overlaying="y", side="right"),
            height=380, margin=dict(l=40, r=40, t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
    else:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=pm["round"], y=pm["expectedGoals"],
                             name="xG", marker_color=color, opacity=0.5))
        fig.add_trace(go.Bar(x=pm["round"], y=pm["expectedAssists"],
                             name="xA", marker_color="#9aa0a6", opacity=0.5))
        fig.add_trace(go.Scatter(x=pm["round"], y=pm["rating"], mode="lines+markers",
                                 name="Rating", line=dict(color="#222", width=2),
                                 yaxis="y2"))
        fig.update_layout(
            xaxis_title="Matchweek",
            yaxis_title="xG / xA per match",
            yaxis2=dict(title="Sofascore rating", overlaying="y", side="right",
                        range=[5, 10]),
            barmode="group",
            height=380, margin=dict(l=40, r=40, t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
    st.plotly_chart(fig, use_container_width=True)

    log_cols = ["round", "venue", "opponent", "minutesPlayed", "rating",
                "expectedGoals", "expectedAssists", "goals", "totalShots",
                "keyPass", "ballRecovery"]
    log_cols = [c for c in log_cols if c in pm.columns]
    log = pm[log_cols].copy()
    for c in log.columns:
        if c in ("round", "minutesPlayed"):
            log[c] = log[c].fillna(0).astype(int)
        elif c in ("venue", "opponent"):
            continue
        else:
            log[c] = log[c].round(2)
    log = log.rename(columns={
        "round": "Round", "venue": "Venue", "opponent": "Opponent",
        "minutesPlayed": "Min",
        "rating": "Rating", "expectedGoals": "xG", "expectedAssists": "xA",
        "goals": "G", "totalShots": "Sh", "keyPass": "KP",
        "ballRecovery": "Recov",
    })
    st.dataframe(log, use_container_width=True, hide_index=True, height=320)
