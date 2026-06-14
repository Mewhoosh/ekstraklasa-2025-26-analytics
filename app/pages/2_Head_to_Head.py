"""Head-to-head page - compare any two clubs."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import (
    team_match_long, load_matches, color_for, FOCUS_COLORS,
)


st.set_page_config(page_title="Head to head", layout="wide")

tm = team_match_long()
teams = sorted(tm["team"].unique())
default_a = teams.index("Jagiellonia Białystok") if "Jagiellonia Białystok" in teams else 0
default_b = teams.index("Lech Poznań") if "Lech Poznań" in teams else 1

st.title("Head to head")

col_a, col_b = st.columns(2)
team_a = col_a.selectbox("Team A", teams, index=default_a)
team_b = col_b.selectbox("Team B", teams, index=default_b)

if team_a == team_b:
    st.warning("Pick two different teams.")
    st.stop()

color_a = color_for(team_a)
color_b = color_for(team_b)

sub_a = tm[tm["team"] == team_a]
sub_b = tm[tm["team"] == team_b]

st.subheader("Season totals")
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"**{team_a}**")
    st.metric("Points", int(sub_a["pts"].sum()))
    st.metric("xPts", f"{sub_a['xpts'].sum():.1f}")
    st.metric("GF / xG", f"{int(sub_a['gf'].sum())} / {sub_a['xg'].sum():.1f}")
    st.metric("GA / xGA", f"{int(sub_a['ga'].sum())} / {sub_a['xga'].sum():.1f}")
with c2:
    st.markdown(f"**{team_b}**")
    st.metric("Points", int(sub_b["pts"].sum()))
    st.metric("xPts", f"{sub_b['xpts'].sum():.1f}")
    st.metric("GF / xG", f"{int(sub_b['gf'].sum())} / {sub_b['xg'].sum():.1f}")
    st.metric("GA / xGA", f"{int(sub_b['ga'].sum())} / {sub_b['xga'].sum():.1f}")

st.subheader("Direct meetings")
matches = load_matches()
direct = matches[
    ((matches["home_team"] == team_a) & (matches["away_team"] == team_b))
    | ((matches["home_team"] == team_b) & (matches["away_team"] == team_a))
].sort_values("date")
if direct.empty:
    st.info("No direct meetings in the dataset.")
else:
    show = direct[["round", "date", "home_team", "home_score", "away_score",
                    "away_team", "home_xg", "away_xg"]].copy()
    show["date"] = show["date"].dt.date
    show = show.rename(columns={
        "round": "Round", "date": "Date",
        "home_team": "Home", "home_score": "H", "away_score": "A",
        "away_team": "Away", "home_xg": "Home xG", "away_xg": "Away xG",
    })
    show["Home xG"] = show["Home xG"].round(2)
    show["Away xG"] = show["Away xG"].round(2)
    st.dataframe(show, use_container_width=True, hide_index=True)

st.subheader("Style fingerprint")
def avg(df, col):
    return df[col].mean()

metrics = {
    "xG":               "xg",
    "Defence (1/xGA)":  None,
    "Possession":       "possession",
    "Shots":            "shots",
    "Touches in box":   "touches_in_box",
    "Recoveries":       "recoveries",
}

def fingerprint(df):
    vals = []
    for label, col in metrics.items():
        if label == "Defence (1/xGA)":
            vals.append(1 / max(df["xga"].mean(), 0.01))
        else:
            vals.append(avg(df, col))
    return vals

league_min = []
league_max = []
for label, col in metrics.items():
    if label == "Defence (1/xGA)":
        per_team = tm.groupby("team")["xga"].mean().rdiv(1)
    else:
        per_team = tm.groupby("team")[col].mean()
    league_min.append(per_team.min())
    league_max.append(per_team.max())


def norm(vals):
    return [(v - lo) / (hi - lo) if hi > lo else 0.5
            for v, lo, hi in zip(vals, league_min, league_max)]

labels = list(metrics.keys())
labels_closed = labels + [labels[0]]
a_norm = norm(fingerprint(sub_a))
b_norm = norm(fingerprint(sub_b))
a_norm_closed = a_norm + [a_norm[0]]
b_norm_closed = b_norm + [b_norm[0]]

fig = go.Figure()
fig.add_trace(go.Scatterpolar(r=a_norm_closed, theta=labels_closed,
                              fill="toself", name=team_a,
                              line=dict(color=color_a, width=2)))
fig.add_trace(go.Scatterpolar(r=b_norm_closed, theta=labels_closed,
                              fill="toself", name=team_b,
                              line=dict(color=color_b, width=2)))
fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1], showticklabels=False)),
                  height=520, margin=dict(l=40, r=40, t=20, b=40))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Cumulative points trajectory")
fig = go.Figure()
for team, sub, color in [(team_a, sub_a, color_a), (team_b, sub_b, color_b)]:
    s = sub.sort_values("round").copy()
    s["cum"] = s["pts"].cumsum()
    fig.add_trace(go.Scatter(x=s["round"], y=s["cum"], mode="lines",
                             name=team, line=dict(color=color, width=3)))
fig.update_layout(xaxis_title="Matchweek", yaxis_title="Cumulative points",
                  height=380, hovermode="x unified",
                  margin=dict(l=40, r=20, t=20, b=40))
st.plotly_chart(fig, use_container_width=True)
