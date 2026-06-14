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

<img width="1174" height="550" alt="obraz" src="https://github.com/user-attachments/assets/370de4ed-e71a-4a46-9880-34176e4e2c77" />

Górnik Zabrze finished 2nd and won the Polish Cup, so the cup winner's Europa League spot rolls down to the next league position - Jagiellonia (3rd) - instead of bumping them to the Conference League.

## 2. Season trajectory

Cumulative Ekstraklasa points by matchweek for each focus club.

<img width="1089" height="490" alt="obraz" src="https://github.com/user-attachments/assets/9124f2a6-9be1-428d-9c63-aabff2340bd5" />

## Form curve

<img width="1089" height="490" alt="obraz" src="https://github.com/user-attachments/assets/26d27c7f-34aa-478b-bfb6-5b1638e286b1" />

## 3. Autumn vs Spring split

Pre- and post-winter break form. Jagiellonia led after autumn; the title was lost in spring.

<img width="889" height="440" alt="obraz" src="https://github.com/user-attachments/assets/31135a2b-238f-47be-82af-4baf1efc110a" />

## 4. Home vs Away performance

PPG by venue. Lech 31k average attendance, Legia 23k, Jaga 18k - does the gate translate to home advantage?

<img width="889" height="437" alt="obraz" src="https://github.com/user-attachments/assets/257b28e3-44e7-408d-9b00-24ed3c65008e" />


## 5. Goals distribution

Result margins, clean sheets, failed-to-score, both-teams-to-score rate per club.

<img width="989" height="381" alt="obraz" src="https://github.com/user-attachments/assets/e3087f0a-df9a-4597-b6c0-30665eb1d7fa" />


## 6. Head-to-head: the six direct matches

Each pair plays twice. Five of the six matches ended in draws - the title race was decided outside the direct meetings.

<img width="516" height="191" alt="obraz" src="https://github.com/user-attachments/assets/cf997a55-0fb9-444f-9744-690aeacf731c" />

<img width="371" height="122" alt="obraz" src="https://github.com/user-attachments/assets/ea2d3aa1-4060-4e41-93fe-8f4cb1405869" />

## 7. Key players

Top contributors per club 

<img width="1390" height="463" alt="obraz" src="https://github.com/user-attachments/assets/70a011e7-663c-43e0-826b-d028bea01dd0" />

and the Legia goalkeeper rotation story (Tobiasz vs Hindrich).

<img width="989" height="440" alt="obraz" src="https://github.com/user-attachments/assets/91e39a4e-7072-4f45-947c-ab8a20ccacba" />

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
