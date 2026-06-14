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

<img width="1302" height="758" alt="obraz" src="https://github.com/user-attachments/assets/594d602d-3d71-4579-ab60-e45575277796" />


Lech sits in the top-left (youngest squad + biggest U21 share) - the champion was also the league's biggest youth investor. Wisła Płock and GKS Katowice are the oldest. Bruk-Bet Termalica gave 0% of minutes to U21 and were relegated.

## 3. League top performers by position

Composite per-90 z-score ranking on objective metrics only - no Sofascore average rating (opaque). Two groups:

<img width="859" height="278" alt="obraz" src="https://github.com/user-attachments/assets/6f6c238d-70f1-44bb-b538-79d1c6f61dda" />

<img width="868" height="208" alt="obraz" src="https://github.com/user-attachments/assets/2d4f1b52-fcde-47b5-b504-292019478d02" />

Output is text tables - no figure.

## 4. Attacking pizzas

Per-90 percentile rank against all attackers (FWD + MID, 900+ minutes) on eight axes: goals, xG, xA, shots, key passes, carries, aerials won, recoveries.

Six attackers featured: Pululu, Bobček, Nowak, Palma, Imaz, Czubak.

<img width="1749" height="1301" alt="obraz" src="https://github.com/user-attachments/assets/b2e1e447-5289-414c-8a40-36fb5ef6a12d" />


## 5. Goalkeeper pizzas

Per-90 percentile rank against all goalkeepers with 900+ minutes. Six axes: goals prevented, saves, pass accuracy, long ball accuracy, long balls volume, recoveries.

Three goalkeepers featured: Cojocaru (Pogoń), Brkić (Motor), Abramowicz (Jagiellonia).

<img width="1633" height="637" alt="obraz" src="https://github.com/user-attachments/assets/d42cb406-c6fd-408e-bf73-b0be3dd53c82" />


## 6. Shot maps - selected attackers

Vertical half-pitch view. Eight attackers - Bobček, Czubak, Ishak, Pululu, Nowak, Palma, Gholizadeh, Imaz. Filled circles are goals, hollow are non-goals, size scaled by xG.

<img width="2189" height="1194" alt="obraz" src="https://github.com/user-attachments/assets/21e80480-3a37-4b71-9e5f-5aafcf4f62da" />


## 7. Statistical similarity

Cosine similarity on the per-90 attacking vector. Picks the closest stylistic matches to a target player across the league. Output is a text table.

Treat as a curiosity, not a serious scouting tool - one season of Sofascore stats is too thin to make hiring decisions on. The Streamlit app exposes the same ranking with user-driven filters (target player, MV cap, age window).

<img width="997" height="261" alt="obraz" src="https://github.com/user-attachments/assets/bcb5f573-a2af-4d76-a233-32cddf727a82" />

---

## Limitations

- Market value is Sofascore's `proposedMarketValueRaw`, not Transfermarkt.
- 900-minute minimum excludes injured / rotation players who may have stronger per-90 metrics on a smaller sample.
- No training or tracking data. The data here is event-aggregated only.
- Position bucketing is coarse (G / D / M / F). Sofascore did not provide finer codes (CB / FB / DM / AM) in the cleaned output.
