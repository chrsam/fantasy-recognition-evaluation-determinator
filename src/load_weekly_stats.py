
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
WEEKLY_STATS_PATH = BASE_DIR / "data" / "player_weekly_stats.csv"
ESPN_SEASON = 2026

def load_weekly_stats():
    """Import historical player fantasy scores into SQLite."""

    # Read the weekly statistics CSV.
    weekly_df = pd.read_csv(WEEKLY_STATS_PATH)

    required_columns = [
        "season",
        "player_id",
        "player_name",
        "week",
        "points",
    ]

    if not set(required_columns).issubset(weekly_df.columns):
        raise ValueError("Missing required weekly statistics columns.")

    if weekly_df.empty:
        raise ValueError("Weekly statistics CSV is empty.")

    if weekly_df[required_columns].isna().any().any():
        raise ValueError("Weekly statistics contain missing values.")

    if weekly_df.duplicated(
        subset=["season", "player_id", "week"]
    ).any():
        raise ValueError("Duplicate player week records detected.")

    if not (weekly_df["season"] == ESPN_SEASON).all():
        raise ValueError("Unexpected season in weekly statistics.")

    if not (weekly_df["week"] > 0).all():
        raise ValueError("Invalid week number detected.")

    collected_at = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        # Confirm the destination table exists.
        table_exists = cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
                AND name = 'player_weekly_stats'
        """).fetchone()

        if not table_exists:
            raise ValueError(
                "player_weekly_stats table does not exist."
            )

        # Synchronize player identities with the master table.
        # Existing player records are preserved.
        unique_players = weekly_df[
            ["player_id", "player_name"]
        ].drop_duplicates(subset=["player_id"])

        player_records = [
            (
                int(row.player_id),
                str(row.player_name),
            )
            for row in unique_players.itertuples(index=False)
        ]

        cursor.executemany("""
            INSERT INTO players (
                player_id,
                player_name
            )
            VALUES (?, ?)
            ON CONFLICT(player_id) DO NOTHING
        """, player_records)


        # Verify that all weekly players now exist.
        existing_ids = {
            row[0]
            for row in cursor.execute(
                "SELECT player_id FROM players"
            )
        }

        missing_ids = (
            set(weekly_df["player_id"].astype(int))
            - existing_ids
        )

        if missing_ids:
            raise ValueError(
                f"Player synchronization failed. "
                f"Missing IDs: {sorted(missing_ids)}"
            )

        # Prepare records for insertion.
        records = [
            (
                int(row.season),
                int(row.player_id),
                int(row.week),
                float(row.points), 
                collected_at,
            )
            for row in weekly_df.itertuples(index=False)
        ]

        cursor.executemany("""
            INSERT INTO player_weekly_stats (
                season,
                player_id,
                week,
                points,
                collected_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(season, player_id, week)
            DO UPDATE SET
                points = excluded.points,
                collected_at = excluded.collected_at
        """, records)

        connection.commit()

        # Verify the imported data.
        total_records = cursor.execute("""
            SELECT COUNT(*)
            FROM player_weekly_stats
            WHERE season = ?
        """, (ESPN_SEASON,)).fetchone()[0]

        unique_players = cursor.execute("""
            SELECT COUNT(DISTINCT player_id)
            FROM player_weekly_stats
            WHERE season = ?
        """, (ESPN_SEASON,)).fetchone()[0]

        week_range = cursor.execute("""
            SELECT MIN(week), MAX(week)
            FROM player_weekly_stats
            WHERE season = ?
        """, (ESPN_SEASON,)).fetchone()

        print("\n===== WEEKLY STATISTICS IMPORT COMPLETE =====")
        print(f"Records processed: {len(records)}")
        print(f"Total stored records: {total_records}")
        print(f"Players with history: {unique_players}")
        print(f"Week range: {week_range[0]}-{week_range[1]}")
        print(f"Import timestamp: {collected_at}")

    finally:
        connection.close()

if __name__ == "__main__":
    load_weekly_stats()
