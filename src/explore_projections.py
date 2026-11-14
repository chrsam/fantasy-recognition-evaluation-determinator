
import sqlite3
import pandas as pd
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"

def explore_projections():
    # Connect to SQLite database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # Retrieve player stats
        query = """
            SELECT
                players.player_name,
                players.position,
                roster_entries.total_points,
                roster_entries.average_points,
                roster_entries.projected_points
            FROM players
            JOIN roster_entries
                ON players.player_id = roster_entries.player_id
            ORDER BY roster_entries.projected_points DESC
        """

        df = pd.read_sql_query(query, connection)

        # Convert scoring columns to numeric
        columns = [
            "total_points",
            "average_points",
            "projected_points"
        ]

        for column in columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        print("===== PROJECTION DATA OVERVIEW =====")
        print(f"Total player records: {len(df)}")

        print("\nMissing values:")
        print(df[columns].isna().sum().to_string())

        print("\nProjection statistics:")
        print(df["projected_points"].describe().round(2))

        print("\n===== ACTUAL VS PROJECTED POINTS =====")

        df['actual_minus_projected'] = (
            df["total_points"] - df["projected_points"]
        )

        print(
            df[
                [
                    "player_name",
                    "position",
                    "total_points",
                    "projected_points",
                    "actual_minus_projected"
                ]
            ].sort_values(
                "projected_points",
                ascending=False
            ).head(15).to_string(index=False)
        )

        print("\n===== TOP 15 PROJECTED PLAYERS =====")
        print(
            df[
                [
                    "player_name",
                    "position",
                    "average_points",
                    "projected_points"
                ]
            ].head(15).to_string(
                index=False
            )
        )

    finally:
        connection.close()

if __name__ == "__main__":
    explore_projections()
