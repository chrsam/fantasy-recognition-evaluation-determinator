
import sqlite3
import pandas as pd
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"

def rank_players():
    # Connect to SQLite database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # Retrieve player stats
        query = """
            SELECT
                players.player_id,
                players.player_name,
                players.position,
                players.nfl_team,
                teams.team_name AS fantasy_team,
                roster_entries.total_points,
                roster_entries.average_points,
                roster_entries.projected_points    
            FROM players
            JOIN roster_entries
                ON players.player_id = roster_entries.player_id
            JOIN teams
                ON roster_entries.fantasy_team_id = teams.team_id
        """

        df = pd.read_sql_query(query, connection)

        # Ensure fantasy point columns are numeric
        point_columns = [
            "total_points",
            "average_points",
            "projected_points"
        ]

        for column in point_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        # Exclude players without average points from rankings
        ranked_df = df.dropna(
            subset=["average_points"]
        ).copy()

        # Calculate overall player rankings
        ranked_df["overall_rank"] = (
            ranked_df["average_points"]
            .rank(method="min", ascending=False)
            .astype(int)
        )

        # Calculate rankings within each position
        ranked_df["position_rank"] = (
            ranked_df.groupby("position")["average_points"]
            .rank(method="min", ascending=False)
            .astype(int)
        )

        # Display top 10 players at each position
        print("===== TOP 10 PLAYERS BY POSITION =====")
        for position in sorted(ranked_df["position"].dropna().unique()):
            position_df = ranked_df[
                ranked_df["position"] == position
            ].sort_values(
                ["position_rank", "player_name"]
            )
            print(f"\n--- {position} ---")
            print(
                position_df[
                    [
                        "position_rank",
                        "player_name",
                        "fantasy_team",
                        "average_points",
                        "total_points"
                    ]
                ].head(10).to_string(index=False)
            )

        # Display top 20 players overall
        print("\n===== TOP 20 PLAYERS OVERALL =====")
        overall_df = ranked_df.sort_values(
            ["overall_rank", "player_name"]
        )
        print(
            overall_df[
                [
                    "overall_rank",
                    "player_name",
                    "position",
                    "fantasy_team",
                    "average_points",
                    "total_points"
                ]
            ].head(20).to_string(index=False)
        )

    finally:
        connection.close()

if __name__ == "__main__":
    rank_players()
