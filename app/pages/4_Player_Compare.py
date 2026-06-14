"""Player compare - pick two players, see pizzas + shot maps side by side
and a per-90 stat comparison table. Two modes: outfield (FWD+MID) and GK.
"""

import numpy as np
import pandas as pd
import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import (
    load_players, load_shots, color_for, JAGA, LECH,
    shot_map_figure, pizza_figure,
)


st.set_page_config(page_title="Player compare", layout="wide")

players = load_players()
shots = load_shots()

st.title("Player compare")
st.caption("Pick any two players. Pizzas and shot maps render side by side.")

mode = st.radio("Mode", ["Outfield (FWD / MID / DEF)", "Goalkeepers"], horizontal=True)


def attack_pool_and_metrics():
    pool = players[
        players["role"].isin(["FWD", "MID", "DEF"]) & (players["minutes"] >= 900)
    ].copy()
    pool["_aerials_p90"] = pool["aerialWon"] / pool["minutes"] * 90
    metrics = {
        "Goals":      "goals_p90",
        "xG":         "xg_p90",
        "xA":         "xa_p90",
        "Shots":      "shots_p90",
        "Key passes": "key_passes_p90",
        "Carries":    "prog_carries_p90",
        "Aerials":    "_aerials_p90",
        "Recoveries": "recoveries_p90",
    }
    for col in metrics.values():
        pool[col] = pool[col].fillna(0)
    return pool, metrics


def gk_pool_and_metrics():
    pool = players[(players["role"] == "GK") & (players["minutes"] >= 900)].copy()
    pool["_gp_p90"]    = pool["goalsPrevented"] / pool["minutes"] * 90
    pool["_saves_p90"] = pool["saves"] / pool["minutes"] * 90
    pool["_pass_acc"]  = pool["accuratePass"] / pool["totalPass"].replace(0, np.nan) * 100
    pool["_lb_acc"]    = pool["accurateLongBalls"] / pool["totalLongBalls"].replace(0, np.nan) * 100
    pool["_lb_p90"]    = pool["totalLongBalls"] / pool["minutes"] * 90
    pool["_recov_p90"] = pool["ballRecovery"] / pool["minutes"] * 90
    metrics = {
        "GP":         "_gp_p90",
        "Saves":      "_saves_p90",
        "Pass acc":   "_pass_acc",
        "LB acc":     "_lb_acc",
        "Long balls": "_lb_p90",
        "Recoveries": "_recov_p90",
    }
    for col in metrics.values():
        pool[col] = pool[col].fillna(0)
    return pool, metrics


if mode == "Goalkeepers":
    pool, PIZZA_METRICS = gk_pool_and_metrics()
    default_a_name = "Valentin Cojocaru"
    default_b_name = "Sławomir Abramowicz"
    stat_metrics = ["_gp_p90", "_saves_p90", "_pass_acc", "_lb_acc", "_lb_p90", "_recov_p90"]
    stat_labels = {
        "_gp_p90": "GP/90", "_saves_p90": "Saves/90",
        "_pass_acc": "Pass acc %", "_lb_acc": "Long ball acc %",
        "_lb_p90": "Long balls/90", "_recov_p90": "Recoveries/90",
    }
else:
    pool, PIZZA_METRICS = attack_pool_and_metrics()
    default_a_name = "Afimico Pululu"
    default_b_name = "Mikael Ishak"
    stat_metrics = ["goals_p90", "xg_p90", "xa_p90", "shots_p90",
                    "key_passes_p90", "prog_carries_p90",
                    "tackles_p90", "interceptions_p90", "recoveries_p90"]
    stat_labels = {
        "goals_p90": "Goals/90", "xg_p90": "xG/90", "xa_p90": "xA/90",
        "shots_p90": "Shots/90", "key_passes_p90": "KP/90",
        "prog_carries_p90": "PrgC/90",
        "tackles_p90": "Tkl/90", "interceptions_p90": "Int/90",
        "recoveries_p90": "Recov/90",
    }

names = sorted(pool["name"].tolist())
if not names:
    st.warning("No players in pool with 900+ minutes.")
    st.stop()

default_a = names.index(default_a_name) if default_a_name in names else 0
default_b = names.index(default_b_name) if default_b_name in names else min(1, len(names) - 1)

c1, c2 = st.columns(2)
name_a = c1.selectbox("Player A", names, index=default_a)
name_b = c2.selectbox("Player B", names, index=default_b)

if name_a == name_b:
    st.warning("Pick two different players.")
    st.stop()

row_a = pool[pool["name"] == name_a].iloc[0]
row_b = pool[pool["name"] == name_b].iloc[0]
color_a = color_for(row_a["team"])
color_b = color_for(row_b["team"])

st.subheader("Headline numbers")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"**{name_a}** ({row_a['team']}, {row_a['role']})")
    a1, a2, a3 = st.columns(3)
    a1.metric("Age", int(row_a["age"]) if pd.notna(row_a["age"]) else "-")
    a2.metric("Minutes", int(row_a["minutes"]))
    a3.metric("MV (EUR)",
              f"{int(row_a['market_value_eur'] or 0):,}" if pd.notna(row_a["market_value_eur"]) else "-")
with col_b:
    st.markdown(f"**{name_b}** ({row_b['team']}, {row_b['role']})")
    b1, b2, b3 = st.columns(3)
    b1.metric("Age", int(row_b["age"]) if pd.notna(row_b["age"]) else "-")
    b2.metric("Minutes", int(row_b["minutes"]))
    b3.metric("MV (EUR)",
              f"{int(row_b['market_value_eur'] or 0):,}" if pd.notna(row_b["market_value_eur"]) else "-")

st.subheader("Pizzas")
col_a, col_b = st.columns(2)
with col_a:
    fig = pizza_figure(row_a, pool, PIZZA_METRICS, color_a, name_a)
    st.plotly_chart(fig, use_container_width=True)
with col_b:
    fig = pizza_figure(row_b, pool, PIZZA_METRICS, color_b, name_b)
    st.plotly_chart(fig, use_container_width=True)

if mode != "Goalkeepers":
    st.subheader("Shot maps")
    col_a, col_b = st.columns(2)
    with col_a:
        s_a = shots[shots["player"] == name_a]
        fig = shot_map_figure(s_a, color_a, name_a)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(s_a)} shots, {int(s_a['is_goal'].sum())} goals, "
                   f"xG {s_a['xg'].sum():.1f}")
    with col_b:
        s_b = shots[shots["player"] == name_b]
        fig = shot_map_figure(s_b, color_b, name_b)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(s_b)} shots, {int(s_b['is_goal'].sum())} goals, "
                   f"xG {s_b['xg'].sum():.1f}")

st.subheader("Per-90 comparison")
rows = []
for m in stat_metrics:
    rows.append({
        "Metric": stat_labels[m],
        name_a: round(row_a.get(m, 0) or 0, 2),
        name_b: round(row_b.get(m, 0) or 0, 2),
    })
cmp = pd.DataFrame(rows)
st.dataframe(cmp, use_container_width=True, hide_index=True)
