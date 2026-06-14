# Notebook 02 - Team Analytics

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1QopjjtC60sVqMAck_5bsQ24gi-VGF7g7?usp=sharing)

League-wide team analytics on Sofascore xG and per-match metrics across all 18 Ekstraklasa clubs. Companion to notebook 01, which ran on FBref counting stats.

Three questions:

1. Which clubs over- or under-performed their underlying numbers?
2. Where does that gap come from - finishing, goalkeeping, or draw luck?
3. How do the 18 clubs cluster by playing style?

## Contents

1. Setup and load
2. League style clustering
3. Tactical fingerprint radar
4. xPts - actual vs expected points
5. Cumulative xPts trajectory
6. Over- and under-performance breakdown
7. Goal sources - open play vs set-piece
8. Shot maps - top clubs
9. Underlying form - rolling xG and xGA
10. Position by matchweek

---

## 2. League style clustering

KMeans on 6 style features (xG, xGA, possession, xG per shot, recoveries, pass accuracy). 4 archetypes. PCA 2D map.

**02_style_clusters.png**

Cluster labels:

- **Attacking** - Lech, Lechia, Raków, Pogoń (highest xG, top shot quality)
- **Defensive** - Legia, Górnik, Cracovia, Widzew (lowest xGA, balanced)
- **Deep-block** - Arka, Zagłębie, Bruk-Bet, GKS, Wisła, Radomiak (least ball, highest xGA, low pressing)
- **Pressing** - Jaga, Korona, Motor, Piast (most recoveries but leaky at the back)

## 3. Tactical fingerprint radar

Six Sofascore metrics for Jaga, Lech and Legia min-max normalised against the league. Defence stored as 1/xGA so higher means better on every axis.

**03_radar.png**

## 4. xPts - actual vs expected points

Per-match expected points via independent Poisson with xG as the rate. Outer product over goal counts gives P(W/D/L), weighted 3/1/0 and summed across the season.

**04_xpts.png**

Jagiellonia's actual minus expected points came out at +11.7 - the largest over-performance in the league.

## 5. Cumulative xPts trajectory

Per matchweek cumulative actual points vs xPts for the three focus clubs. Filled bands show the running gap.

**05_xpts_trajectory.png**

## 6. Over- and under-performance breakdown

Standings sorted by actual points with expected position and the gap decomposed into finishing (GF vs xG) and defending (GA vs xGA). Plus goalkeeper over- and under-performance (Sofascore goals prevented).

**06_xpts_table.png** (HTML styled table - screenshot to embed)

**06_goalkeeper.png**

Jaga's goalkeeper Abramowicz contributed +3.8 goals prevented. Lechia's GK posted -12.7 - catastrophic. Korona +10.0 was the biggest GK over-performance in the league.

## 7. Goal sources - open play vs set-piece

Share of season xG by situation per team. Sorted by set-piece dependency.

**07_goal_sources.png**

Set-piece-heavy: Zagłębie (40%) and GKS Katowice (38%). Set-piece-light: Lech (17%) and Jaga (20%).

## 8. Shot maps - top clubs

Vertical half-pitch view for Lech, Jaga, Legia, Lechia. Each circle is one shot, size scaled by xG, filled circles are goals.

**08_shot_maps.png**

## 9. Underlying form - rolling xG and xGA

5-match rolling xG created and xGA conceded for the three focus clubs.

**09_rolling_xg.png**

Jaga's xGA sat above xG for most of the season - underlying form was poor despite the third-place finish.

## 10. Position by matchweek

League position by matchweek for the focus clubs. Relegation zone and European spots shaded. Two views - title race and mid-table battle.

**10_bump_chart.png**

**10b_bump_chart_bottom.png**

Legia spent multiple matchweeks in the relegation zone before climbing back to mid-table by the end of the season. Exact matchweeks depend on the tie-break used (we apply Ekstraklasa's head-to-head rule).

---

## Limitations

- Sofascore xG, not Opta or StatsBomb. Reasonable for in-league comparison but not directly comparable to top-5 leagues.
- KMeans labels are interpretive, not algorithmic. Silhouette is mild (~0.23), expected for 18 teams in one league.
- Single season, no time-decay across years.


