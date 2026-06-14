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

st.subheader("Shot map - club total")
shots = load_shots()
club_shots = shots[shots["team"] == club]
fig = shot_map_figure(club_shots, color)
st.plotly_chart(fig, use_container_width=True)
st.caption(f"{len(club_shots)} shots, {int(club_shots['is_goal'].sum())} goals, "
           f"xG total {club_shots['xg'].sum():.1f}")

st.subheader("Top contributors (goals + assists)")
players = load_players()
club_players = players[players["team"] == club].copy()
club_players["ga"] = club_players["goals"].fillna(0) + club_players.get("assists", 0).fillna(0)
top = club_players.sort_values("ga", ascending=False).head(10)[
    ["name", "lineup_position", "age", "minutes", "goals", "xg", "xa", "avg_rating"]
].copy()
top["minutes"] = top["minutes"].fillna(0).astype(int)
top["goals"] = top["goals"].fillna(0).astype(int)
top["xg"] = top["xg"].round(1)
top["xa"] = top["xa"].round(2)
top["avg_rating"] = top["avg_rating"].round(2)
top = top.rename(columns={"name": "Name", "lineup_position": "Pos",
                          "age": "Age", "minutes": "Min", "goals": "G",
                          "xg": "xG", "xa": "xA", "avg_rating": "Rating"})
st.dataframe(top, use_container_width=True, hide_index=True)
