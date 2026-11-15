
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
FREE_AGENTS_PATH = BASE_DIR / "data" / "free_agents.csv"
ESPN_SEASON = 2026

def clean_value(value):
    """Convert pandas missing values to None."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value

def ensure_column(connection, table, column, definition):
    """Add a db column only if it doesn't already exist"""
    existing_columns = [
        row[1]
        for row in connection.execute(
            f"PRAGMA table_info({table})"
        )
    ]

    if column not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )

def load_free_agents():
    # Read free-agent csv
    free_agents_df = pd.read_csv(FREE_AGENTS_PATH)

    # Create one timestamp for this collection
    collected_at = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    # Connect to database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        # Create free-agent snapshot table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS free_agent_snapshots (
            season INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            collected_at TEXT NOT NULL,
            total_points REAL,
            average_points REAL,
            projected_points REAL,
            projected_avg_points REAL,
            projected_total_points REAL,
            injury_status TEXT,
            percent_owned REAL,
            percent_started REAL,

            PRIMARY KEY (
                season,
                player_id,
                collected_at
            ),

            FOREIGN KEY (player_id)
                REFERENCES players(player_id)
            )
        """)

        # Add new columns if they don't already exist
        ensure_column(
            connection, "free_agent_snapshots",
            "active_status", "TEXT"
        )

        # Insert or update player records
        for _, player in free_agents_df.iterrows():
            cursor.execute("""
                INSERT INTO free_agent_snapshots (
                    season,
                    player_id,
                    collected_at,
                    total_points,
                    average_points,
                    projected_points,
                    projected_avg_points,
                    projected_total_points,
                    injury_status,
                    percent_owned,
                    percent_started,
                    active_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    season,
                    player_id,
                    collected_at
                ) DO UPDATE SET
                    total_points = excluded.total_points,
                    average_points = excluded.average_points,
                    projected_points = excluded.projected_points,
                    projected_avg_points = excluded.projected_avg_points,
                    projected_total_points = excluded.projected_total_points,
                    injury_status = excluded.injury_status,
                    percent_owned = excluded.percent_owned,
                    percent_started = excluded.percent_started,
                    active_status = excluded.active_status
            """, (
                ESPN_SEASON,
                int(player["player_id"]),
                collected_at,
                clean_value(player["total_points"]),
                clean_value(player["average_points"]),
                clean_value(player["projected_points"]),
                clean_value(player["projected_avg_points"]),
                clean_value(player["projected_total_points"]),
                clean_value(player["injury_status"]),
                clean_value(player["percent_owned"]),
                clean_value(player["percent_started"]),
                clean_value(player["active_status"])
            ))

        # Insert free agent snapshots
        for _, player in free_agents_df.iterrows():
            cursor.execute("""            
                INSERT INTO free_agent_snapshots (
                    season,
                    player_id,
                    collected_at,
                    total_points,
                    average_points,
                    projected_points,
                    projected_avg_points,
                    projected_total_points,
                    injury_status,
                    percent_owned,
                    percent_started
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    season,
                    player_id,
                    collected_at
                ) DO UPDATE SET
                    total_points = excluded.total_points,
                    average_points = excluded.average_points,
                    projected_points = excluded.projected_points,
                    projected_avg_points = excluded.projected_avg_points,
                    projected_total_points = excluded.projected_total_points,
                    injury_status = excluded.injury_status,
                    percent_owned = excluded.percent_owned,
                    percent_started = excluded.percent_started
            """, (
                ESPN_SEASON,
                int(player["player_id"]),
                collected_at,
                clean_value(player["total_points"]),
                clean_value(player["average_points"]),
                clean_value(player["projected_points"]),
                clean_value(player["projected_avg_points"]),
                clean_value(player["projected_total_points"]),
                clean_value(player["injury_status"]),
                clean_value(player["percent_owned"]),
                clean_value(player["percent_started"])
            ))

        connection.commit()

        # Verify imported records
        player_count = cursor.execute("""
            SELECT COUNT(*)
            FROM players
        """).fetchone()[0]

        snapshot_count = cursor.execute("""        
            SELECT COUNT(*)
            FROM free_agent_snapshots
            WHERE season = ?
                AND collected_at = ?
        """,(ESPN_SEASON, collected_at)).fetchone()[0]    

        print("===== FREE AGENT IMPORT COMPLETE =====")
        print(f"Players in the master table: {player_count}")
        print(f"Free agent snapshots imported: {snapshot_count}")
        print(f"Collection timestamp: {collected_at}")

    finally:
        connection.close()

if __name__ == "__main__":
    load_free_agents()
