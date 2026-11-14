
import sqlite3
import pandas as pd
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"

def explore_database():
    # Connect to SQLite database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # Retrieve player and roster information
        query = """
            SELECT
                players.player_id,
                players.player_name,
                players.position,
                players.nfl_team,
                teams.team_name AS fantasy_team,
                roster_entries.lineup_slot,
                roster_entries.total_points,
                roster_entries.average_points,
                roster_entries.projected_points
            FROM players
            JOIN roster_entries
                ON players.player_id = roster_entries.player_id
            JOIN teams
                ON roster_entries.fantasy_team_id = teams.team_id
            ORDER BY players.position, players.player_name
        """   

        df = pd.read_sql_query(query, connection)

        # Basic dataset information
        print("===== DATASET OVERVIEW =====")
        print(f"Total player records: {len(df)}")
        print(f"Total columns: {len(df.columns)}")

        print("\nColumn Names:")
        print(df.columns.tolist())

        print("\nData Types:")
        print(df.dtypes)

        # Player distribution by position
        print("\n===== PLAYERS BY POSITION =====")
        position_counts = (
            df.groupby("position")["player_id"]
            .nunique()
            .sort_values(ascending=False)
        )
        print(position_counts)

        # Fantasy points summary
        print("\n===== FANTASY POINTS SUMMARY =====")
        print(
            df.groupby("position")[
                ["total_points", "average_points", "projected_points"]
            ].agg(["count", "mean", "median", "max"]).round(2)
        )

        # Missing data
        print("\n===== MISSING DATA =====")
        print(df.isnull().sum())

        # Highest-scoring players
        print("\n===== TOP 10 PLAYERS BY AVERAGE POINTS =====")
        top_players = df.sort_values(
            "average_points",
            ascending=False
        ).head(10)

        print(
            top_players[
                [
                    "player_name",
                    "position",
                    "fantasy_team",
                    "average_points",
                    "total_points"
                ]
            ].to_string(index=False)
        )

    finally:
        connection.close()

if __name__ == "__main__":
    explore_database()
