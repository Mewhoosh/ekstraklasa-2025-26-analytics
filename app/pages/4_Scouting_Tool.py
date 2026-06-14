"""KNN scouting tool - cosine similarity on a per-90 attacking vector."""

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import load_players


st.set_page_config(page_title="Scouting Tool", layout="wide")

players = load_players()

SIM_FEATURES = [
    "goals_p90", "xg_p90", "xa_p90", "shots_p90",
    "key_passes_p90", "prog_carries_p90",
    "tackles_p90", "interceptions_p90", "recoveries_p90",
]

st.title("Statistical similarity")
st.caption(
    "Cosine similarity on a per-90 vector. Picks the closest stylistic matches "
    "to a target player across the league. Treat as a curiosity, not a hiring tool."
)

pool = players[
    players["role"].isin(["FWD", "MID"]) & (players["minutes"] >= 900)
].copy()
for f in SIM_FEATURES:
    pool[f] = pool[f].fillna(0)

c1, c2 = st.columns([2, 1])
target = c1.selectbox("Target player", sorted(pool["name"].tolist()),
                      index=sorted(pool["name"].tolist()).index("Afimico Pululu")
                      if "Afimico Pululu" in pool["name"].values else 0)
top_n = c2.slider("Top N", 5, 20, 10)

c1, c2, c3 = st.columns(3)
exclude_same_team = c1.checkbox("Exclude same team", value=True)
mv_max_pct = c2.slider("Max MV vs target (%)", 25, 300, 100)
age_window = c3.slider("Age window (years +/-)", 1, 15, 6)

scaler = StandardScaler()
X = scaler.fit_transform(pool[SIM_FEATURES])
sim = cosine_similarity(X)

target_idx = pool.index[pool["name"] == target][0]
target_row = pool.loc[target_idx]
pool["similarity"] = sim[pool.index.get_loc(target_idx)]

target_mv = target_row["market_value_eur"] or 0
mv_cap = target_mv * mv_max_pct / 100 if target_mv else None
target_age = target_row["age"]

candidates = pool[pool["name"] != target].copy()
if exclude_same_team:
    candidates = candidates[candidates["team"] != target_row["team"]]
if mv_cap is not None:
    candidates = candidates[candidates["market_value_eur"].fillna(0) <= mv_cap]
candidates = candidates[
    (candidates["age"] >= target_age - age_window)
    & (candidates["age"] <= target_age + age_window)
]
candidates = candidates.sort_values("similarity", ascending=False).head(top_n)

st.subheader(f"Target: {target}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Team", target_row["team"])
c2.metric("Age", int(target_row["age"]) if pd.notna(target_row["age"]) else "-")
c3.metric("Minutes", int(target_row["minutes"]))
c4.metric("MV (EUR)", f"{int(target_mv):,}" if target_mv else "-")

st.subheader(f"Top {len(candidates)} similar (filters applied)")
cols = ["name", "team", "role", "age", "minutes", "market_value_eur",
        "similarity", "goals_p90", "xg_p90", "xa_p90", "key_passes_p90"]
out = candidates[cols].copy()
out["minutes"] = out["minutes"].astype(int)
out["market_value_eur"] = out["market_value_eur"].fillna(0).astype(int)
out["similarity"] = out["similarity"].round(3)
for c in ["goals_p90", "xg_p90", "xa_p90", "key_passes_p90"]:
    out[c] = out[c].round(2)
out = out.rename(columns={
    "name": "Name", "team": "Team", "role": "Role", "age": "Age",
    "minutes": "Min", "market_value_eur": "MV (EUR)",
    "similarity": "Similarity",
    "goals_p90": "G/90", "xg_p90": "xG/90", "xa_p90": "xA/90",
    "key_passes_p90": "KP/90",
})
st.dataframe(out, use_container_width=True, hide_index=True)
