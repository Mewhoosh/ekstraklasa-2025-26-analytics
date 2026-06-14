"""xPts simulator - sliders for xG_for and xG_against, real-time outcome
distribution and expected points."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import xpts_for


st.set_page_config(page_title="xPts simulator", layout="wide")

st.title("xPts simulator")
st.caption(
    "Pick xG values for both sides. The Poisson model computes P(W/D/L) and "
    "the expected points return. Same maths the team analytics notebook uses."
)

c1, c2 = st.columns(2)
xg_for = c1.slider("xG (your team)", 0.0, 5.0, 1.5, step=0.1)
xg_against = c2.slider("xG (opponent)", 0.0, 5.0, 1.0, step=0.1)

result = xpts_for(xg_for, xg_against)

c1, c2, c3, c4 = st.columns(4)
c1.metric("P(win)", f"{result['p_win']*100:.1f}%")
c2.metric("P(draw)", f"{result['p_draw']*100:.1f}%")
c3.metric("P(loss)", f"{result['p_loss']*100:.1f}%")
c4.metric("xPts", f"{result['xpts']:.2f}")

st.subheader("Outcome distribution")
fig = go.Figure()
fig.add_trace(go.Bar(
    x=["Win", "Draw", "Loss"],
    y=[result["p_win"], result["p_draw"], result["p_loss"]],
    marker_color=["#3aa757", "#d97706", "#d75b5b"],
    text=[f"{result['p_win']*100:.1f}%",
          f"{result['p_draw']*100:.1f}%",
          f"{result['p_loss']*100:.1f}%"],
    textposition="outside",
))
fig.update_layout(yaxis_title="Probability", yaxis_range=[0, 1],
                  height=400, margin=dict(l=40, r=20, t=20, b=40),
                  showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Method")
st.markdown(
    """
    1. Goal counts modelled as independent Poisson, mean = xG.
    2. Joint distribution of (your goals, opp goals) = outer product of the two pmfs.
    3. Sum the lower triangle for P(win), the diagonal for P(draw), the upper
       triangle for P(loss).
    4. Expected points = 3 * P(win) + 1 * P(draw).

    Cap on goals: 8 per side, enough for the tail to be negligible.
    """
)
