# Notebook 03 - Player Analytics

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1KGek1qdDoax2bLRj304S-fehQ5f11iN6?usp=sharing)

Sofascore per-player aggregates and per-match metrics across all 18 clubs. Companion to notebook 02 - same data layer, shifted from teams to individual players.

## Contents

1. Setup and load
2. Squad demographics
3. League top performers by position
4. Attacking pizzas
5. Goalkeeper pizzas
6. Shot maps - selected attackers
7. Statistical similarity

---

## 2. Squad demographics

Minutes-weighted average squad age vs share of minutes given to under-21 players. Top-left of the scatter is a young squad, bottom-right is a veteran one.

**02_demographics.png**

Lech sits in the top-left (youngest squad + biggest U21 share) - the champion was also the league's biggest youth investor. Wisła Płock and GKS Katowice are the oldest. Bruk-Bet Termalica gave 0% of minutes to U21 and were relegated.

## 3. League top performers by position

Composite per-90 z-score ranking on objective metrics only - no Sofascore average rating (opaque). Two groups:

- **Attacking players** (FWD + MID): goals, xG, xA, shots, key passes, progressive carries.
- **Goalkeepers**: goals prevented per 90, saves per 90.

Output is text tables - no figure.

## 4. Attacking pizzas

Per-90 percentile rank against all attackers (FWD + MID, 900+ minutes) on eight axes: goals, xG, xA, shots, key passes, carries, aerials won, recoveries.

Six attackers featured: Pululu, Bobček, Nowak, Palma, Imaz, Czubak.

**04_pizzas_attackers.png**

## 5. Goalkeeper pizzas

Per-90 percentile rank against all goalkeepers with 900+ minutes. Six axes: goals prevented, saves, pass accuracy, long ball accuracy, long balls volume, recoveries.

Three goalkeepers featured: Cojocaru (Pogoń), Brkić (Motor), Abramowicz (Jagiellonia).

**05_pizzas_gks.png**

## 6. Shot maps - selected attackers

Vertical half-pitch view. Eight attackers - Bobček, Czubak, Ishak, Pululu, Nowak, Palma, Gholizadeh, Imaz. Filled circles are goals, hollow are non-goals, size scaled by xG.

**06_shot_maps.png**

## 7. Statistical similarity

Cosine similarity on the per-90 attacking vector. Picks the closest stylistic matches to a target player across the league. Output is a text table.

Treat as a curiosity, not a serious scouting tool - one season of Sofascore stats is too thin to make hiring decisions on. The Streamlit app exposes the same ranking with user-driven filters (target player, MV cap, age window).

---

## Limitations

- Market value is Sofascore's `proposedMarketValueRaw`, not Transfermarkt.
- 900-minute minimum excludes injured / rotation players who may have stronger per-90 metrics on a smaller sample.
- No training or tracking data. The data here is event-aggregated only.
- Position bucketing is coarse (G / D / M / F). Sofascore did not provide finer codes (CB / FB / DM / AM) in the cleaned output.
