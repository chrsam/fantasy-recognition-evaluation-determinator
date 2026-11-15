
import sqlite3
import pandas as pd
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
FREE_AGENTS_PATH = BASE_DIR / "data" / "free_agents.csv"

def validate_free_agents():
    # Load free agent csv
    free_agents_df = pd.read_csv(FREE_AGENTS_PATH)

    # Connect to SQLite database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # Retrieve rostered player IDs
        rostered_df = pd.read_sql_query(
            # "SELECT player_id FROM roster_entries",
            # connection
            """
            SELECT 
                re.player_id,
                p.player_name AS roster_player_name,
                p.position AS roster_position,
                t.team_name AS fantasy_team_name,
                re.lineup_slot
            FROM roster_entries re
            JOIN players p
                ON re.player_id = p.player_id
            JOIN teams t
                ON re.fantasy_team_id = t.team_id
            """,
            connection
        )

        free_agent_ids = set(
            free_agents_df["player_id"].dropna()
        )

        rostered_ids = set(
            rostered_df["player_id"].dropna()
        )

        # Check for overlap
        overlapping_ids = free_agent_ids.intersection(
            rostered_ids
        )

        if overlapping_ids:
            print("\n===== OVERLAPPING PLAYER DETAILS =====")

            overlapping_df = free_agents_df[
                free_agents_df["player_id"].isin(overlapping_ids)
            ].merge(
                rostered_df,
                on="player_id",
                how="left"
            )

            print(
                overlapping_df[
                    [
                        "player_id",
                        "player_name",
                        "roster_position",
                        "fantasy_team_name",
                        "lineup_slot",
                        "on_team_id"
                    ]
                ].to_string(index=False)
            )

        # Check fantasy team assignments
        assigned_players = (
            free_agents_df["on_team_id"] != 0
        ).sum()

        print("===== FREE AGENT VALIDATION =====")
        print(
            f"Free agents: {len(free_agent_ids)}"
        )
        print(
            f"Rostered players: {len(rostered_ids)}"
        )
        print(
            f"Players assigned to fantasy teams: "
            f"{assigned_players}"
        )
        print(
            f"Players appearing in both datasets: "
            f"{len(overlapping_ids)}"
        )
        if overlapping_ids:
            print("\nOverlapping player IDs:")
            print(overlapping_ids)
        else:
            print("\nNo overlapping players found.")

    finally:
        connection.close()

if __name__ == "__main__":
    validate_free_agents()
