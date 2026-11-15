
import sqlite3
import pandas as pd
from pathlib import Path

# Locate project files
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
ROSTERS_CSV_PATH = BASE_DIR / "data" / "rosters.csv"

# League configuration
ESPN_SEASON=2026

def clean_value(value):
    """
    Convert pandas missing values to None
    and NumPy values to standard Python values.
    """
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value

def load_roster_data():
    # Read roster information
    rosters_df = pd.read_csv(ROSTERS_CSV_PATH)

    # Connect to database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        # Create a list of unique players
        players_df = rosters_df.drop_duplicates(
            subset=["player_id"]
        )

        # Remove existing roster entries for this season
        cursor.execute("""
            DELETE FROM roster_entries
            WHERE season = ?
        """, (ESPN_SEASON,))

        # Insert or update player records
        for _, player in players_df.iterrows():
            cursor.execute("""
                INSERT INTO players (
                    player_id,
                    player_name,
                    position,
                    nfl_team
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    player_name = excluded.player_name,
                    position = excluded.position,
                    nfl_team = excluded.nfl_team
            """, (
                int(player["player_id"]),
                clean_value(player["player_name"]),
                clean_value(player["position"]),
                clean_value(player["nfl_team"])
            ))

        # Insert or update roster entries
        for _, player in rosters_df.iterrows():
            cursor.execute("""
                INSERT INTO roster_entries (
                    season,
                    fantasy_team_id,
                    player_id,
                    lineup_slot,
                    acquisition_type,
                    injury_status,
                    total_points,
                    average_points,
                    projected_points
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    season,
                    fantasy_team_id,
                    player_id
                ) DO UPDATE SET
                    lineup_slot = excluded.lineup_slot,
                    acquisition_type = excluded.acquisition_type,
                    injury_status = excluded.injury_status,
                    total_points = excluded.total_points,
                    average_points = excluded.average_points,
                    projected_points = excluded.projected_points
            """,(
                ESPN_SEASON,
                int(player["fantasy_team_id"]),
                int(player["player_id"]),
                clean_value(player["lineup_slot"]),
                clean_value(player["acquisition_type"]),
                clean_value(player["injury_status"]),
                clean_value(player["total_points"]),
                clean_value(player["average_points"]),
                clean_value(player["projected_points"])
            ))

        connection.commit()

        # Verify imported records
        player_count = cursor.execute(
            "SELECT COUNT(*) FROM players"
        ).fetchone()[0]

        roster_count = cursor.execute(
            "SELECT COUNT(*) FROM roster_entries"
        ).fetchone()[0]

        missing_nfl_team = cursor.execute("""
            SELECT COUNT(*)
            FROM players
            WHERE nfl_team IS NULL
        """).fetchone()[0]

        print("Player and roster data imported successfully!")
        print(f"Unique players: {player_count}")
        print(f"Roster entries: {roster_count}") 
        print(f"Players without an NFL team: {missing_nfl_team}")               


    finally:
        connection.close()

if __name__ == "__main__":
    load_roster_data()
