
import sqlite3
import pandas as pd
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
ESPN_SEASON = 2026

def compare_player_stats():
    # Connect to database
    connection = sqlite3.connect(DATABASE_PATH) 

    try:
        query = """
            SELECT
                p.player_id,
                p.player_name,
                p.position,
                re.average_points AS roster_average_points,
                fas.average_points AS free_agent_average_points
            FROM players p
            LEFT JOIN roster_entries re
                ON p.player_id = re.player_id
                AND re.season = ?
            LEFT JOIN free_agent_snapshots fas
                ON p.player_id = fas.player_id
                AND fas.season = ?
                AND fas.collected_at = (
                    SELECT MAX(fas2.collected_at)
                    FROM free_agent_snapshots fas2
                    where FAS2.player_id = p.player_id
                    AND fas2.season = ?
                )
            WHERE re.player_id IS NOT NULL
                OR fas.player_id IS NOT NULL
        """

        df = pd.read_sql_query(
            query,
            connection,
            params=(ESPN_SEASON, ESPN_SEASON, ESPN_SEASON)
        )

        print("===== PLAYER STATISTICS COMPARISON =====")
        print(f"Players analyzed: {len(df)}")

        # Identify players w/ stats in both datasets
        overlapping_stats = df.dropna(
            subset=[
                "roster_average_points",
                "free_agent_average_points"
            ]
        ).copy()

        print(
            "\nPlayers w/ stats in both datasets:",
            len(overlapping_stats)
        )

        if not overlapping_stats.empty:
            overlapping_stats["difference"] = (
                overlapping_stats["roster_average_points"]
                - overlapping_stats["free_agent_average_points"]
            )
            print("\nSample comparisons:")
            print(
                overlapping_stats[
                    [
                        "player_name",
                        "position",
                        "roster_average_points",
                        "free_agent_average_points",
                        "difference"
                    ]
                ].head(20).to_string(index=False)
            )
            print("\nDifference summary:")
            print(
                overlapping_stats["difference"].describe().to_string()
            )
        else:
            print(
                "\nNo overlapping player stats available "
                "for direct comparison."
            )

        print("\nMissing roster averages:")
        print(df["roster_average_points"].isna().sum())

        print("\nMissing free agent averages:")
        print(df["free_agent_average_points"].isna().sum())

    finally:
        connection.close()


if __name__ == "__main__":
    compare_player_stats()
