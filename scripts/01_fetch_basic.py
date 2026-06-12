"""Fetch Ekstraklasa basic results from football-data.co.uk and save locally."""

from pathlib import Path

import pandas as pd

URL = "https://www.football-data.co.uk/new/POL.csv"
OUT = Path(__file__).parent.parent / "data" / "raw" / "ekstraklasa_results_full.csv"


def main() -> None:
    print(f"Fetching {URL}")
    df = pd.read_csv(URL)
    print(f"  {len(df)} matches across {df['Season'].nunique()} seasons")

    df_2526 = df[df["Season"] == "2025/2026"]
    print(f"  2025-26: {len(df_2526)} matches")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved to {OUT}")


if __name__ == "__main__":
    main()
