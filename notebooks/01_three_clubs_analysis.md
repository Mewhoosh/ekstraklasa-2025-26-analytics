# Notebook 01 - Three Clubs Analysis

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1WkE71OOVvHdRSHehyfqPhypmKhN91K0A?usp=sharing)

Basic comparative analysis of three Polish top-flight clubs across the 2025/26 Ekstraklasa season. Runs on FBref counting stats only - this notebook predates the Sofascore scrape, so there is no xG, no xA and no advanced metrics. Limited what you can do with that. The xG-driven analysis is in notebooks 02 and 03.

- **Lech Poznań** - champion, 60 pts (Champions League qualification)
- **Jagiellonia Białystok** - 3rd, 56 pts (Europa League via league)
- **Legia Warsaw** - 6th, 49 pts (no European football)

Data sources: FBref (scraped via Chrome DevTools Protocol to bypass Cloudflare) and football-data.co.uk for match cross-checks.

## Contents

1. League snapshot
2. Season trajectory
3. Autumn vs Spring split
4. Home vs Away performance
5. Goals distribution
6. Head-to-head: the six direct matches
7. Key players

---

## 1. League snapshot

Final standings with three target clubs colour-coded. Headline numbers per club in a focus table.

**01_league_snapshot.png**

## 2. Season trajectory

Cumulative Ekstraklasa points by matchweek for each focus club.

**02_season_trajectory.png**

## 3. Autumn vs Spring split

Pre- and post-winter break form. Jagiellonia led after autumn; the title was lost in spring.

**03_autumn_spring.png**

## 4. Home vs Away performance

PPG by venue. Lech 31k average attendance, Legia 23k, Jaga 18k - does the gate translate to home advantage?

**04_home_away.png**

## 5. Goals distribution

Result margins, clean sheets, failed-to-score, both-teams-to-score rate per club.

**05_goals_distribution.png**

## 6. Head-to-head: the six direct matches

Each pair plays twice. Five of the six matches ended in draws - the title race was decided outside the direct meetings.

**06_head_to_head.png**

## 7. Key players

Top contributors per club and the Legia goalkeeper rotation story (Tobiasz vs Hindrich).

**07_key_players.png**

---

## Headline findings

- Five of six head-to-head matches ended in draws.
- Legia's goalkeeper split. Tobiasz 1.00 PPG (relegation form). Hindrich 2.15 PPG (above Lech's title-winning starter).
- Jagiellonia were autumn leaders. PPG fell from 1.71 to 1.59 in the spring half.
- Legia had no finisher. Top scorer Rajović managed only 6 goals.

## Limitations

- **No xG / xA for Ekstraklasa on FBref.** FBref dropped advanced metrics for the league after the Opta feed change. This notebook runs on counting stats only - that is the reason notebooks 02 and 03 exist.
- **Hindrich finding is correlation.** Legia changed three coaches during the season.

## Target-club colours

- Lech Poznań - `royalblue`
- Jagiellonia - `crimson`
- Legia Warsaw - `forestgreen`
