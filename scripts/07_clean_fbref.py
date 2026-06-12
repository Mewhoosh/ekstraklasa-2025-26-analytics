"""Identify FBref tables by their column structure and save them with semantic names.

The raw scrape dumps every table on each page. The first ~9 tables on a team page
are FBref's sidebar widgets (other leagues' standings) - noise. The rest are the
actual player- and team-level stats, but their index varies by team because FBref
sometimes splits Ekstraklasa-only vs All-Competitions or shows extra panels.

This cleaner reads every raw CSV, classifies it by columns, and writes only the
meaningful ones to data/processed/ with names like:
    jagiellonia_player_standard.csv
    jagiellonia_match_log.csv
    league_standings.csv
"""

import re
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent.parent / "data" / "raw"
OUT = Path(__file__).parent.parent / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)


def col_set(df: pd.DataFrame) -> set[str]:
    """Flatten multi-level headers and also expose the last-level name on its own.

    FBref tables come with two-row headers, e.g. ('Performance', 'Gls'). After
    read_csv with header=[0,1] this lands as a MultiIndex of tuples. We include
    both the joined form ("Performance/Gls") and the last component ("Gls") so
    the downstream classifier can match either way.
    """
    cols: set[str] = set()
    for c in df.columns:
        if isinstance(c, tuple):
            parts = [str(p) for p in c if not str(p).startswith("Unnamed")]
            if parts:
                cols.add("/".join(parts))
                cols.add(parts[-1])
        else:
            s = str(c)
            if not s.startswith("Unnamed"):
                cols.add(s)
                # Compound names like "Performance/Gls" -> also expose "Gls"
                if "/" in s:
                    cols.add(s.split("/")[-1])
    return cols


def classify(df: pd.DataFrame) -> str | None:
    """Return a semantic table name based on column structure, or None to skip.

    Order matters: each kind is identified by columns that are unique to it.
    """
    cols = col_set(df)
    n_rows = len(df)

    # 1. Sidebar widget - tiny tables with 3 cols
    if df.shape == (4, 3) or (n_rows <= 6 and df.shape[1] == 3):
        return None

    # 2. Match log - "Comp" (competition) and "Opponent" are unique to match logs
    if "Comp" in cols and "Opponent" in cols and "Venue" in cols and "Result" in cols:
        return "match_log"

    # 3. Home/Away standings split - "Home/MP" and "Away/MP" are unique markers
    if "Home/MP" in cols and "Away/MP" in cols:
        return "standings_home_away"

    # 4. League standings - "Top Team Scorer" and "Goalkeeper" are unique to FBref
    # league standings tables
    if "Top Team Scorer" in cols and "Squad" in cols and n_rows >= 15:
        return "standings"

    # 5. Player goalkeeping - "SoTA" (shots on target against) only in GK tables
    if "Player" in cols and "SoTA" in cols and "Save%" in cols:
        return "player_goalkeeping"

    # 6. Player shooting - "SoT%" and "G/Sh" only in shooting tables
    if "Player" in cols and "SoT%" in cols:
        return "player_shooting"

    # 7. Player misc - "Fls" (fouls) and "Fld" (fouled) only in misc
    if "Player" in cols and "Fls" in cols and "Fld" in cols:
        return "player_misc"

    # 8. Player playing time - "Mn/Start" only in playing time table
    if "Player" in cols and "Mn/Start" in cols:
        return "player_playing_time"

    # 9. Player standard stats - last fallback for player tables
    if "Player" in cols and "Gls" in cols and "Ast" in cols and "90s" in cols:
        return "player_standard"

    # 10. League squad-level summary tables (no Player column)
    if "Squad" in cols and "Player" not in cols and n_rows >= 15:
        if "GA90" in cols:
            return "squad_goalkeeping"
        if "SoT%" in cols:
            return "squad_shooting"
        if "Fls" in cols and "Fld" in cols:
            return "squad_misc"
        if "Gls" in cols and "Ast" in cols:
            return "squad_standard"

    return None


def team_from_filename(path: Path) -> str:
    """fbref_jagiellonia_05_xxx.csv -> jagiellonia"""
    parts = path.stem.split("_")
    # parts[0] == "fbref", parts[1] starts the team key, then digits
    name_parts = []
    for p in parts[1:]:
        if p.isdigit():
            break
        name_parts.append(p)
    return "_".join(name_parts)


def main() -> None:
    csvs = sorted(RAW.glob("fbref_*.csv"))
    print(f"Scanning {len(csvs)} raw csvs in {RAW}")

    counts: dict[str, int] = {}
    written: list[Path] = []

    for csv in csvs:
        team = team_from_filename(csv)
        try:
            # Try reading with first row as header; some tables need header=[0,1]
            df = pd.read_csv(csv)
        except Exception as e:
            print(f"  skip {csv.name} (read error: {e})")
            continue

        # If columns look like multi-level header collapsed, try re-reading
        if df.columns[0].startswith("Unnamed"):
            try:
                df = pd.read_csv(csv, header=[0, 1])
            except Exception:
                pass

        kind = classify(df)
        if kind is None:
            continue

        out_name = f"{team}_{kind}.csv"
        # Avoid overwriting: if same kind already written for this team, suffix
        target = OUT / out_name
        if target.exists():
            # The Ekstraklasa-only and All-Competitions tables can both classify
            # the same. Keep the larger one.
            existing = pd.read_csv(target)
            if len(df) <= len(existing):
                continue
        df.to_csv(target, index=False)
        written.append(target)
        counts[kind] = counts.get(kind, 0) + 1

    print(f"\nWrote {len(written)} processed csvs to {OUT}")
    print("\nBy kind:")
    for kind, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {kind:<25} {n}")


if __name__ == "__main__":
    main()
