"""Club profile page - one club, multiple angles in one view."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import (
    team_match_long, load_shots, load_players,
    color_for, shot_map_figure,
)


st.set_page_config(page_title="Club Profile", layout="wide")

tm = team_match_long()
teams = sorted(tm["team"].unique())

club = st.sidebar.selectbox("Club", teams, index=teams.index("Jagiellonia Białystok"))
color = color_for(club)

sub = tm[tm["team"] == club].sort_values("round").copy()
sub["cum_pts"] = sub["pts"].cumsum()
sub["cum_xpts"] = sub["xpts"].cumsum()
sub["roll_xg"] = sub["xg"].rolling(5, min_periods=1).mean()
sub["roll_xga"] = sub["xga"].rolling(5, min_periods=1).mean()

st.title(club)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Points", int(sub["pts"].sum()))
c2.metric("xPts", f"{sub['xpts'].sum():.1f}")
c3.metric("Pts - xPts", f"{(sub['pts'].sum() - sub['xpts'].sum()):+.1f}")
c4.metric("GF / xG", f"{int(sub['gf'].sum())} / {sub['xg'].sum():.1f}")
c5.metric("GA / xGA", f"{int(sub['ga'].sum())} / {sub['xga'].sum():.1f}")

st.subheader("Actual vs expected points trajectory")
fig = go.Figure()
fig.add_trace(go.Scatter(x=sub["round"], y=sub["cum_pts"], mode="lines",
                         name="Actual", line=dict(color=color, width=3)))
fig.add_trace(go.Scatter(x=sub["round"], y=sub["cum_xpts"], mode="lines",
                         name="Expected", line=dict(color=color, width=2, dash="dash"),
                         opacity=0.6))
fig.update_layout(xaxis_title="Matchweek", yaxis_title="Cumulative points",
                  height=420, hovermode="x unified",
                  margin=dict(l=40, r=20, t=20, b=40))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Rolling 5-match xG and xGA")
fig = go.Figure()
fig.add_trace(go.Scatter(x=sub["round"], y=sub["roll_xg"], mode="lines",
                         name="xG created", line=dict(color=color, width=3)))
fig.add_trace(go.Scatter(x=sub["round"], y=sub["roll_xga"], mode="lines",
                         name="xGA conceded",
                         line=dict(color=color, width=2, dash="dash"),
                         opacity=0.6))
fig.update_layout(xaxis_title="Matchweek", yaxis_title="xG / xGA per match",
                  height=380, hovermode="x unified",
                  margin=dict(l=40, r=20, t=20, b=40))
st.plotly_chart(fig, use_container_width=True)

shots = load_shots()
st.subheader("Shot map - club total")
club_shots_all = shots[shots["team"] == club]
fig = shot_map_figure(club_shots_all, color)
st.plotly_chart(fig, use_container_width=True)
st.caption(f"{len(club_shots_all)} shots, {int(club_shots_all['is_goal'].sum())} goals, "
           f"xG total {club_shots_all['xg'].sum():.1f}")

st.subheader("Goal sources by situation")
club_shots = shots[shots["team"] == club].copy()

OPEN_PLAY = {"assisted", "regular"}
SET_PIECE = {"corner", "set-piece", "free-kick", "throw-in-set-piece"}
FAST_BREAK = {"fast-break"}
PENALTY = {"penalty"}

def bucket(s):
    if s in OPEN_PLAY: return "Open play"
    if s in SET_PIECE: return "Set piece"
    if s in FAST_BREAK: return "Fast break"
    if s in PENALTY: return "Penalty"
    return "Other"

club_shots["bucket"] = club_shots["situation"].map(bucket)
src = club_shots.groupby("bucket")["xg"].sum().reindex(
    ["Open play", "Fast break", "Set piece", "Penalty"]).fillna(0)
total_xg = src.sum() or 1
palette = {"Open play": "#4f7cc0", "Fast break": "#d97706",
           "Set piece": "#9333ea", "Penalty": "#7a8a99"}

fig = go.Figure()
left = 0
for bucket_name in ["Open play", "Fast break", "Set piece", "Penalty"]:
    val = src[bucket_name]
    share = val / total_xg
    fig.add_trace(go.Bar(
        y=[club], x=[share], orientation="h",
        marker_color=palette[bucket_name], name=bucket_name,
        text=f"{share*100:.0f}%", textposition="inside",
        textfont=dict(color="white"),
    ))
fig.update_layout(
    barmode="stack", xaxis=dict(range=[0, 1], tickformat=".0%"),
    height=180, margin=dict(l=10, r=10, t=10, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="left", x=0),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Form - match log")
log = sub[["round", "date", "venue", "opp", "gf", "ga", "xg", "xga", "result", "pts"]].copy()
log["date"] = log["date"].dt.date
log["xg"] = log["xg"].round(2)
log["xga"] = log["xga"].round(2)
log = log.rename(columns={
    "round": "MW", "date": "Date", "venue": "V", "opp": "Opponent",
    "gf": "GF", "ga": "GA", "xg": "xG", "xga": "xGA",
    "result": "Res", "pts": "Pts",
})
st.dataframe(log, use_container_width=True, hide_index=True, height=380)

st.subheader("Top contributors (goals + assists)")
players = load_players()
club_players = players[players["team"] == club].copy()
assists_col = "assists" if "assists" in club_players.columns else "goalAssist"
club_players["_ga_total"] = (club_players["goals"].fillna(0)
                              + club_players[assists_col].fillna(0))
club_players["_xga_total"] = (club_players["xg"].fillna(0)
                              + club_players["xa"].fillna(0))
top = club_players.sort_values("_ga_total", ascending=False).head(10)[
    ["name", "lineup_position", "age", "minutes",
     "goals", assists_col, "_ga_total", "xg", "xa", "_xga_total"]
].copy()
top["minutes"] = top["minutes"].fillna(0).astype(int)
top["goals"] = top["goals"].fillna(0).astype(int)
top[assists_col] = top[assists_col].fillna(0).astype(int)
top["_ga_total"] = top["_ga_total"].fillna(0).astype(int)
top["xg"] = top["xg"].round(1)
top["xa"] = top["xa"].round(2)
top["_xga_total"] = top["_xga_total"].round(1)
top = top.rename(columns={"name": "Name", "lineup_position": "Pos",
                          "age": "Age", "minutes": "Min",
                          "goals": "G", assists_col: "A",
                          "_ga_total": "G+A",
                          "xg": "xG", "xa": "xA",
                          "_xga_total": "xG+xA"})
st.dataframe(top, use_container_width=True, hide_index=True)


st.subheader("Records and extremes")

club_matches = tm[tm["team"] == club].copy()
club_matches["margin"] = club_matches["gf"] - club_matches["ga"]
club_matches["xg_diff"] = club_matches["xg"] - club_matches["xga"]
club_matches["overperf"] = club_matches["pts"] - club_matches["xpts"]

def _show(df, cols, n=10):
    out = df[cols].copy()
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"]).dt.date
    for c in ("xg", "xga", "xg_diff"):
        if c in out.columns:
            out[c] = out[c].round(2)
    return out.head(n).rename(columns={
        "round": "Round", "date": "Date", "opp": "Opponent", "venue": "V",
        "gf": "GF", "ga": "Opp G", "xg": "xG", "xga": "Opp xG",
        "margin": "Margin", "xg_diff": "xG diff",
    })

t1, t2, t3, t4 = st.tabs([
    "Wins / losses",
    "xG domination / battered",
    "Streaks",
    "Scrappy / unlucky",
])

with t1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Biggest wins**")
        wins = club_matches[club_matches["margin"] > 0].sort_values("margin", ascending=False)
        st.dataframe(_show(wins,
                           ["round", "date", "venue", "opp", "gf", "ga", "margin", "xg", "xga"]),
                     use_container_width=True, hide_index=True)
    with col_b:
        st.markdown("**Heaviest losses**")
        losses = club_matches[club_matches["margin"] < 0].sort_values("margin")
        st.dataframe(_show(losses,
                           ["round", "date", "venue", "opp", "gf", "ga", "margin", "xg", "xga"]),
                     use_container_width=True, hide_index=True)

with t2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Biggest xG dominations**")
        dom = club_matches.sort_values("xg_diff", ascending=False)
        st.dataframe(_show(dom,
                           ["round", "date", "venue", "opp", "xg", "xga", "xg_diff", "gf", "ga"]),
                     use_container_width=True, hide_index=True)
    with col_b:
        st.markdown("**Biggest xG batterings received**")
        bat = club_matches.sort_values("xg_diff")
        st.dataframe(_show(bat,
                           ["round", "date", "venue", "opp", "xg", "xga", "xg_diff", "gf", "ga"]),
                     use_container_width=True, hide_index=True)

with t3:
    cm = club_matches.sort_values("round")
    cs_runs, ft_runs = [], []
    cs_cur, ft_cur = 0, 0
    for _, r in cm.iterrows():
        if r["ga"] == 0:
            cs_cur += 1
        else:
            if cs_cur > 0:
                cs_runs.append({"Length": cs_cur, "Ended round": r["round"]})
            cs_cur = 0
        if r["gf"] == 0:
            ft_cur += 1
        else:
            if ft_cur > 0:
                ft_runs.append({"Length": ft_cur, "Ended round": r["round"]})
            ft_cur = 0
    if cs_cur > 0:
        cs_runs.append({"Length": cs_cur, "Ended round": "ongoing"})
    if ft_cur > 0:
        ft_runs.append({"Length": ft_cur, "Ended round": "ongoing"})
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Clean sheet streaks**")
        if cs_runs:
            st.dataframe(pd.DataFrame(cs_runs).sort_values("Length", ascending=False),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No clean sheets recorded.")
    with col_b:
        st.markdown("**Failed-to-score streaks**")
        if ft_runs:
            st.dataframe(pd.DataFrame(ft_runs).sort_values("Length", ascending=False),
                         use_container_width=True, hide_index=True)
        else:
            st.info("Scored in every match.")

with t4:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Scrappiest wins** (3 pts despite low xG)")
        scrap = club_matches[club_matches["pts"] == 3].sort_values("overperf", ascending=False)
        st.dataframe(_show(scrap,
                           ["round", "date", "venue", "opp", "gf", "ga", "xg", "xga"]),
                     use_container_width=True, hide_index=True)
    with col_b:
        st.markdown("**Unluckiest losses** (high xG, no points)")
        unlucky = club_matches[club_matches["pts"] == 0].sort_values("overperf")
        st.dataframe(_show(unlucky,
                           ["round", "date", "venue", "opp", "gf", "ga", "xg", "xga"]),
                     use_container_width=True, hide_index=True)
