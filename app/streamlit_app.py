"""Ekstraklasa 2025/26 Analytics - Streamlit app entry.

Home page: league overview with the xPts standings table and a few headline
numbers. Detailed views live under pages/.
"""

import streamlit as st
import plotly.express as px

from utils import (
    load_standings, team_match_long, FOCUS_COLORS, color_for,
)


st.set_page_config(
    page_title="Ekstraklasa 2025/26",
    page_icon=":soccer:",
    layout="wide",
)


st.title("Ekstraklasa 2025/26 - Analytics")
st.caption(
    "Sofascore xG, FBref counting stats and per-player aggregates across "
    "all 18 clubs. Pick a page on the left for a focused view, or stay here "
    "for the league overview."
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
season = season.sort_values(["pts", "gd", "gf"], ascending=[False, False, False]).reset_index(drop=True)
season["pos"] = season.index + 1


col1, col2, col3 = st.columns(3)
champ = season.iloc[0]
col1.metric("Champion", champ["team"], f"{int(champ['pts'])} pts")

top_over = season.sort_values("diff", ascending=False).iloc[0]
col2.metric("Biggest over-performance", top_over["team"], f"+{top_over['diff']:.1f} pts vs xPts")

top_under = season.sort_values("diff").iloc[0]
col3.metric("Biggest under-performance", top_under["team"], f"{top_under['diff']:.1f} pts vs xPts")


st.subheader("xPts standings")

display = season[["pos", "team", "pts", "xpts", "diff", "gf", "xg", "ga", "xga"]].copy()
display = display.rename(columns={
    "pos": "Pos", "team": "Team", "pts": "Pts", "xpts": "xPts",
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
        "Pts - xPts": st.column_config.NumberColumn(
            "Pts - xPts",
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
    size_max=18,
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


st.caption(
    "Method: per-match expected points via independent Poisson with xG as "
    "the rate. Outer product over goal counts gives P(W/D/L), weighted "
    "3/1/0 and summed across the season."
)
