# Notebook 02 - Team Analytics

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1QopjjtC60sVqMAck_5bsQ24gi-VGF7g7?usp=sharing)

League-wide team analytics on Sofascore xG and per-match metrics across all 18 Ekstraklasa clubs. Companion to notebook 01, which ran on FBref counting stats.

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

<img width="1301" height="814" alt="obraz" src="https://github.com/user-attachments/assets/4ba23ea9-e7ee-4bb0-901a-e4b10653f0ff" />


Cluster labels:

- **Attacking** - Lech, Lechia, Raków, Pogoń (highest xG, top shot quality)
- **Defensive** - Legia, Górnik, Cracovia, Widzew (lowest xGA, balanced)
- **Deep-block** - Arka, Zagłębie, Bruk-Bet, GKS, Wisła, Radomiak (least ball, highest xGA, low pressing)
- **Pressing** - Jaga, Korona, Motor, Piast (most recoveries but leaky at the back)

## 3. Tactical fingerprint radar

Six Sofascore metrics for Jaga, Lech and Legia min-max normalised against the league. Defence stored as 1/xGA so higher means better on every axis.

<img width="972" height="819" alt="obraz" src="https://github.com/user-attachments/assets/a80d272e-a7a0-4644-b5f7-c8e4a2e6f982" />


## 4. xPts - actual vs expected points

Per-match expected points via independent Poisson with xG as the rate. Outer product over goal counts gives P(W/D/L), weighted 3/1/0 and summed across the season.

<img width="1746" height="790" alt="obraz" src="https://github.com/user-attachments/assets/a32ca2f5-c881-4f64-b349-ed24b026ef12" />


Jagiellonia's actual minus expected points came out at +11.7 - the largest over-performance in the league.

## 5. Cumulative xPts trajectory

Per matchweek cumulative actual points vs xPts for the three focus clubs. Filled bands show the running gap.

<img width="1746" height="566" alt="obraz" src="https://github.com/user-attachments/assets/96b3e757-48b6-4ac4-a1a5-5ca272e7d0a6" />


## 6. Over- and under-performance breakdown

Standings sorted by actual points with expected position and the gap decomposed into finishing (GF vs xG) and defending (GA vs xGA). Plus goalkeeper over- and under-performance (Sofascore goals prevented).

<img width="902" height="584" alt="obraz" src="https://github.com/user-attachments/assets/33bc3890-dc16-45b1-8669-a2aab749fd07" />

<img width="1089" height="703" alt="obraz" src="https://github.com/user-attachments/assets/42ffdc97-7ea2-4506-a512-bee144cb9f0b" />


Jaga's goalkeeper Abramowicz contributed +3.8 goals prevented. Lechia's GK posted -12.7 - catastrophic. Pogoń +7.5 was the biggest GK over-performance in the league.

## 7. Goal sources - open play vs set-piece

Share of season xG by situation per team. Sorted by set-piece dependency.

<img width="1308" height="821" alt="obraz" src="https://github.com/user-attachments/assets/33d184ce-a35a-4ffd-9723-288c0a63827a" />


Set-piece-heavy: Zagłębie (40%) and GKS Katowice (38%). Set-piece-light: Lech (17%) and Jaga (20%).

## 8. Shot maps - top clubs

Vertical half-pitch view for Lech, Jaga, Legia, Lechia. Each circle is one shot, size scaled by xG, filled circles are goals.

<img width="1968" height="570" alt="obraz" src="https://github.com/user-attachments/assets/22d5af3d-f56a-4a6e-b8a3-53fae370e470" />


## 9. Underlying form - rolling xG and xGA

5-match rolling xG created and xGA conceded for the three focus clubs.

<img width="1746" height="566" alt="obraz" src="https://github.com/user-attachments/assets/ec6d7d77-a9fc-4ab3-b212-3710c51550db" />

Jaga's xGA sat above xG for most of the season - underlying form was poor despite the third-place finish.

## 10. Position by matchweek

League position by matchweek for the focus clubs. Relegation zone and European spots shaded. Two views - title race and mid-table battle.

<img width="1418" height="758" alt="obraz" src="https://github.com/user-attachments/assets/ee11e172-8d4d-48c0-b890-699661b51703" />

<img width="1418" height="758" alt="obraz" src="https://github.com/user-attachments/assets/3a3f6f8e-dea6-4983-87d0-c0149fc4c3c7" />

<img width="1418" height="758" alt="obraz" src="https://github.com/user-attachments/assets/9303cbe8-7d31-42ce-b9a3-e757fd4036b3" />

Legia spent multiple matchweeks in the relegation zone before climbing back to mid-table by the end of the season. Exact matchweeks depend on the tie-break used (we apply Ekstraklasa's head-to-head rule).

---

## Limitations

- Sofascore xG, not Opta or StatsBomb. Reasonable for in-league comparison but not directly comparable to top-5 leagues.
- KMeans labels are interpretive, not algorithmic. Silhouette is mild (~0.23), expected for 18 teams in one league.
- Single season, no time-decay across years.


