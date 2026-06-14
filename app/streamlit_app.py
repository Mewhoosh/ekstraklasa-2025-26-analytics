"""Ekstraklasa 2025/26 Analytics - Streamlit app entry.

Home page: league overview with the xPts standings table, headline metrics
and a per-club position history picker. Detailed views live under pages/.
"""

import numpy as np
import pandas as pd
import plotly.colors as pcolors
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from utils import (
    FOCUS_COLORS, color_for, team_match_long, standings_at,
)


st.set_page_config(
    page_title="Ekstraklasa 2025/26",
    page_icon=":soccer:",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.info(
    "Use the sidebar on the left to switch between pages - Club Profile, "
    "Head-to-Head, Player Explorer, Player Compare, Scouting Tool. This "
    "page is the league overview.",
    icon="👈",
)
st.title("Ekstraklasa 2025/26 - Analytics")
st.caption(
    "Sofascore xG, FBref counting stats and per-player aggregates across "
    "all 18 clubs."
)


tm = team_match_long()
season = (tm.groupby("team", as_index=False)
            .agg(pts=("pts", "sum"),
                 xpts=("xpts", "sum"),
                 gf=("gf", "sum"),
                 ga=("ga", "sum"),
                 xg=("xg", "sum"),
                 xga=("xga", "sum")))
season["diff"] = season["pts"] - season["xpts"]
season["gd"] = season["gf"] - season["ga"]

final_pos = standings_at(tm, 34)[["team", "pos"]]
season = season.merge(final_pos, on="team").sort_values("pos").reset_index(drop=True)

xpos_order = season.sort_values("xpts", ascending=False).reset_index(drop=True)
xpos_order["xpos"] = xpos_order.index + 1
season = season.merge(xpos_order[["team", "xpos"]], on="team")
season["pos_swing"] = season["xpos"] - season["pos"]


col1, col2, col3 = st.columns(3)
champ = season.iloc[0]
col1.metric("Champion", champ["team"], f"{int(champ['pts'])} pts")
top_over = season.sort_values("diff", ascending=False).iloc[0]
col2.metric("Biggest over-performance", top_over["team"], f"+{top_over['diff']:.1f} pts vs xPts")
top_under = season.sort_values("diff").iloc[0]
col3.metric("Biggest under-performance", top_under["team"], f"{top_under['diff']:.1f} pts vs xPts")


st.subheader("Standings - actual and expected")

display = season[["pos", "xpos", "pos_swing", "team", "pts", "xpts", "diff",
                  "gf", "xg", "ga", "xga"]].copy()
display = display.rename(columns={
    "pos": "Pos", "xpos": "xPos", "pos_swing": "Swing",
    "team": "Team", "pts": "Pts", "xpts": "xPts",
    "diff": "Pts - xPts", "gf": "GF", "xg": "xG", "ga": "GA", "xga": "xGA",
})
display["xPts"] = display["xPts"].round(1)
display["Pts - xPts"] = display["Pts - xPts"].round(1)
display["xG"] = display["xG"].round(1)
display["xGA"] = display["xGA"].round(1)

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Swing": st.column_config.NumberColumn(
            help="xPos minus Pos. Positive = should be higher by xPts.",
            format="%+d",
        ),
        "Pts - xPts": st.column_config.NumberColumn(
            help="Actual points minus expected points. Positive = over-performed.",
            format="%+.1f",
        ),
    },
)


st.subheader("Points vs expected points")
fig = px.scatter(
    season,
    x="xpts", y="pts",
    hover_name="team",
    color=season["team"].map(FOCUS_COLORS).fillna("#5a6470"),
    color_discrete_map="identity",
)
fig.update_traces(marker=dict(size=14, line=dict(width=1.5, color="white")))
lo = min(season["xpts"].min(), season["pts"].min()) - 2
hi = max(season["xpts"].max(), season["pts"].max()) + 2
fig.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi,
              line=dict(color="#bbb", dash="dash", width=1))
fig.update_layout(
    xaxis_title="Expected points (xPts)",
    yaxis_title="Actual points",
    showlegend=False,
    height=520,
    margin=dict(l=40, r=20, t=20, b=40),
)
st.plotly_chart(fig, use_container_width=True)


st.subheader("Position by matchweek")
all_rounds = sorted(tm["round"].unique())
pos_records = []
for r in all_rounds:
    t = standings_at(tm, r)
    t["round"] = r
    pos_records.append(t[["round", "team", "pos", "pts"]])
pos_df = pd.concat(pos_records, ignore_index=True)

c1, c2 = st.columns([2, 3])
picked = c1.multiselect(
    "Highlight clubs",
    sorted(tm["team"].unique()),
    default=["Jagiellonia Białystok", "Lech Poznań", "Legia Warszawa"],
)

fig = go.Figure()
for team in pos_df["team"].unique():
    if team in picked:
        continue
    sub = pos_df[pos_df["team"] == team]
    fig.add_trace(go.Scatter(
        x=sub["round"], y=sub["pos"], mode="lines",
        line=dict(color="#d0d4d8", width=1),
        showlegend=False, hovertext=team, hoverinfo="text+x+y",
    ))
for team in picked:
    sub = pos_df[pos_df["team"] == team]
    fig.add_trace(go.Scatter(
        x=sub["round"], y=sub["pos"], mode="lines",
        name=team, line=dict(color=color_for(team), width=3),
        hovertext=team, hoverinfo="text+x+y",
    ))

fig.add_shape(type="rect", x0=0.5, x1=34.5, y0=15.5, y1=18.5,
              line=dict(width=0), fillcolor="#d75b5b", opacity=0.08)
fig.add_shape(type="rect", x0=0.5, x1=34.5, y0=0.5, y1=5.5,
              line=dict(width=0), fillcolor="#3aa757", opacity=0.08)
fig.update_layout(
    xaxis_title="Matchweek", yaxis_title="Position",
    yaxis=dict(autorange="reversed", tickmode="linear", dtick=1),
    height=520, margin=dict(l=40, r=20, t=20, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Red band = relegation zone (16-18). Green band = European spots (1-5)."
)


st.subheader("xPts breakdown table")
st.caption(
    "Standings sorted by actual points with expected position and the gap "
    "decomposed into finishing (GF vs xG) and defending (GA vs xGA). "
    "Green = over-performed, red = under-performed."
)

_break = season.copy()
_break["xgd"] = _break["xg"] - _break["xga"]
_break["finishing"] = _break["gf"] - _break["xg"]
_break["defending"] = _break["xga"] - _break["ga"]
_break["MP"] = 34
_break = _break.sort_values("pos").reset_index(drop=True)
_break = _break[["team", "pos", "xpos", "pos_swing", "MP", "pts", "xpts", "diff",
                 "gf", "xg", "finishing", "ga", "xga", "defending", "gd", "xgd"]]


def _cell_color(value, vmin, vmax):
    if pd.isna(value):
        return "rgb(245,245,245)"
    t = (value - vmin) / (vmax - vmin)
    t = max(0.0, min(1.0, t))
    return pcolors.sample_colorscale("RdYlGn", t)[0]


COLOURED = {
    "pos_swing": (-10, 10),
    "diff": (-12, 12),
    "finishing": (-13, 13),
    "defending": (-15, 15),
}

display_cols = ["team", "pos", "xpos", "pos_swing", "MP", "pts", "xpts", "diff",
                "gf", "xg", "finishing", "ga", "xga", "defending", "gd", "xgd"]
header_labels = ["Team", "Pos", "xPos", "Swing", "MP", "Pts", "xPts", "Pts diff",
                 "GF", "xG", "Finishing", "GA", "xGA", "Defending", "GD", "xGD"]

cell_values = []
cell_colors = []
for col in display_cols:
    values = _break[col].tolist()
    if col == "team":
        cell_values.append(values)
        cell_colors.append(["white"] * len(values))
        continue
    if col in ("pos", "xpos", "MP", "pts", "gd", "gf", "ga"):
        cell_values.append([int(v) for v in values])
        cell_colors.append(["white"] * len(values))
        continue
    if col == "pos_swing":
        cell_values.append([f"{int(v):+d}" for v in values])
    elif col in ("diff", "finishing", "defending", "xgd"):
        cell_values.append([f"{v:+.1f}" for v in values])
    else:
        cell_values.append([f"{v:.1f}" for v in values])
    if col in COLOURED:
        lo, hi = COLOURED[col]
        cell_colors.append([_cell_color(v, lo, hi) for v in values])
    else:
        cell_colors.append(["white"] * len(values))

fig = go.Figure(data=[go.Table(
    header=dict(values=[f"<b>{l}</b>" for l in header_labels],
                fill_color="#1f2937", font=dict(color="white", size=12),
                align="center", height=32),
    cells=dict(values=cell_values, fill_color=cell_colors,
               align=["left"] + ["center"] * (len(display_cols) - 1),
               font=dict(color="#222", size=12), height=28),
    columnwidth=[200] + [60] * (len(display_cols) - 1),
)])
fig.update_layout(height=680, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)


st.subheader("Style clusters")
st.caption(
    "KMeans (k=4) on per-match averages across six style features, projected "
    "into a 2D PCA plane. Take the cluster labels with a pinch of salt - "
    "silhouette score is mild (around 0.22), expected for 18 teams in a "
    "single league. The map still shows neighbourhoods of similar style."
)

team_stats = tm.groupby("team").agg(
    xg=("xg", "mean"),
    xga=("xga", "mean"),
    possession=("possession", "mean"),
    xg_per_shot=("xg", lambda s: s.sum() / tm.loc[s.index, "shots"].sum()),
    recoveries=("recoveries", "mean"),
    pass_acc=("acc_passes", lambda s: s.sum() / tm.loc[s.index, "passes"].sum()),
).reset_index()
_feat = ["xg", "xga", "possession", "xg_per_shot", "recoveries", "pass_acc"]
X = StandardScaler().fit_transform(team_stats[_feat])
km = KMeans(n_clusters=4, n_init=30, random_state=42).fit(X)
team_stats["cluster"] = km.labels_
_pca = PCA(n_components=2, random_state=42)
xy = _pca.fit_transform(X)
team_stats["pc1"] = xy[:, 0]
team_stats["pc2"] = xy[:, 1]
CLUSTER_LABELS = {0: "Attacking", 1: "Defensive", 2: "Deep-block", 3: "Pressing"}
CLUSTER_COLORS = {0: "#d97706", 1: "#0a6b3a", 2: "#7a8a99", 3: "#9333ea"}
team_stats["archetype"] = team_stats["cluster"].map(CLUSTER_LABELS)

fig = go.Figure()
for cid, label in CLUSTER_LABELS.items():
    sub = team_stats[team_stats["cluster"] == cid]
    hover = [
        f"<b>{r['team']}</b><br>"
        f"xG {r['xg']:.2f} | xGA {r['xga']:.2f}<br>"
        f"Possession {r['possession']:.1f}%<br>"
        f"xG/shot {r['xg_per_shot']:.3f}<br>"
        f"Recoveries {r['recoveries']:.1f}<br>"
        f"Pass acc {r['pass_acc']:.1%}"
        for _, r in sub.iterrows()
    ]
    fig.add_trace(go.Scatter(
        x=sub["pc1"], y=sub["pc2"], mode="markers+text",
        marker=dict(size=18, color=CLUSTER_COLORS[cid],
                    line=dict(color="white", width=1.5)),
        text=sub["team"], textposition="top center",
        name=f"{label} (n={len(sub)})",
        hovertext=hover, hoverinfo="text",
    ))
fig.add_hline(y=0, line=dict(color="#bbb", width=0.7))
fig.add_vline(x=0, line=dict(color="#bbb", width=0.7))
fig.update_layout(
    xaxis_title=f"PC1 ({_pca.explained_variance_ratio_[0]:.0%}) - attacking output",
    yaxis_title=f"PC2 ({_pca.explained_variance_ratio_[1]:.0%}) - press intensity",
    height=560, margin=dict(l=40, r=20, t=20, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, use_container_width=True)


st.subheader("Records and extremes - league wide")
st.caption(
    "Single-side rankings only - the symmetric losses tables for the whole "
    "league are the same matches from the opposite team's perspective. "
    "Switch to a club profile for the both-sided view."
)

tm["margin"] = tm["gf"] - tm["ga"]
tm["xg_diff"] = tm["xg"] - tm["xga"]

def _show(df, cols, n=10):
    out = df[cols].copy()
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"]).dt.date
    for c in ("xg", "xga", "xg_diff"):
        if c in out.columns:
            out[c] = out[c].round(2)
    return out.head(n).rename(columns={
        "round": "Round", "date": "Date", "team": "Team", "opp": "Opponent",
        "venue": "V", "gf": "GF", "ga": "Opp G", "xg": "xG", "xga": "Opp xG",
        "margin": "Margin", "xg_diff": "xG diff",
    })

t1, t2, t3, t4 = st.tabs([
    "Biggest wins",
    "Biggest xG dominations",
    "Clean sheet / failed-to-score streaks",
    "Scrappy wins / unlucky losses",
])

with t1:
    big = tm[tm["margin"] > 0].sort_values("margin", ascending=False)
    st.dataframe(_show(big,
                       ["round", "date", "team", "venue", "opp", "gf", "ga", "margin", "xg", "xga"]),
                 use_container_width=True, hide_index=True)

with t2:
    dom = tm.sort_values("xg_diff", ascending=False)
    st.dataframe(_show(dom,
                       ["round", "date", "team", "venue", "opp", "xg", "xga", "xg_diff", "gf", "ga"]),
                 use_container_width=True, hide_index=True)

with t3:
    cs, fts = [], []
    for team, sub in tm.sort_values(["team", "round"]).groupby("team"):
        cs_run = ft_run = 0
        cs_best = ft_best = 0
        cs_end = ft_end = None
        for _, r in sub.iterrows():
            if r["ga"] == 0:
                cs_run += 1
                if cs_run > cs_best:
                    cs_best = cs_run
                    cs_end = r["round"]
            else:
                cs_run = 0
            if r["gf"] == 0:
                ft_run += 1
                if ft_run > ft_best:
                    ft_best = ft_run
                    ft_end = r["round"]
            else:
                ft_run = 0
        cs.append({"Team": team, "Streak": cs_best, "Ended round": cs_end})
        fts.append({"Team": team, "Streak": ft_best, "Ended round": ft_end})
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Longest clean sheet streaks**")
        st.dataframe(pd.DataFrame(cs).sort_values("Streak", ascending=False),
                     use_container_width=True, hide_index=True, height=420)
    with col_b:
        st.markdown("**Longest failed-to-score streaks**")
        st.dataframe(pd.DataFrame(fts).sort_values("Streak", ascending=False),
                     use_container_width=True, hide_index=True, height=420)

with t4:
    tm["overperf"] = tm["pts"] - tm["xpts"]
    scrap = tm[tm["pts"] == 3].sort_values("overperf", ascending=False)
    st.markdown("**Scrappiest wins** (3 points despite low xG)")
    st.dataframe(_show(scrap,
                       ["round", "date", "team", "venue", "opp", "gf", "ga", "xg", "xga"]),
                 use_container_width=True, hide_index=True)
    unlucky = tm[tm["pts"] == 0].sort_values("overperf")
    st.markdown("**Unluckiest losses** (high xG, no points)")
    st.dataframe(_show(unlucky,
                       ["round", "date", "team", "venue", "opp", "gf", "ga", "xg", "xga"]),
                 use_container_width=True, hide_index=True)
