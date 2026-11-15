
import sqlite3
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
ESPN_SEASON = 2026

def verify_free_agents():
    # Connect to database
    connection = sqlite3.connect(DATABASE_PATH)    

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        # Identify the latest collection timestamp
        latest_timestamp = cursor.execute("""
            SELECT MAX(collected_at)
            FROM free_agent_snapshots
            WHERE season = ?
        """,(ESPN_SEASON,)).fetchone()[0]

        # Count latest snapshot records
        snapshot_count = cursor.execute("""
            SELECT COUNT(*)
            FROM free_agent_snapshots
            WHERE season = ?
                AND collected_at = ?
        """,(ESPN_SEASON, latest_timestamp)).fetchone()[0]

        # Count unique players in latest snapshot
        unique_players = cursor.execute("""
            SELECT COUNT(DISTINCT player_id)
            FROM free_agent_snapshots
            WHERE season = ?
                AND collected_at = ?
        """,(ESPN_SEASON, latest_timestamp)).fetchone()[0]

        # Position breakdown
        position_counts = cursor.execute("""
            SELECT p.position, COUNT(*)
            FROM free_agent_snapshots fas
            JOIN players p
                ON fas.player_id = p.player_id
            WHERE fas.season = ?
                AND fas.collected_at = ?
            GROUP BY p.position
            ORDER BY p.position
        """,(ESPN_SEASON, latest_timestamp)).fetchall()

        # Check for overlap w/ current rosters
        overlap_count = cursor.execute("""
            SELECT COUNT(*)
            FROM free_agent_snapshots fas
            JOIN roster_entries re
                ON fas.player_id = re.player_id
                AND fas.season = re.season
            WHERE fas.season = ?
                AND fas.collected_at = ?
        """,(ESPN_SEASON, latest_timestamp)).fetchone()[0]   

        # Check foreign key integrity
        foreign_key_errors = cursor.execute("""
            PRAGMA foreign_key_check
        """).fetchall()

        print("===== FREE AGENT DATABASE VALIDATION =====")  

        print(f"Latest collection: {latest_timestamp}")
        print(f"Snapshot records: {snapshot_count}")
        print(f"Unique players: {unique_players}")

        print("\nPlayers by position:")
        for position, count in position_counts:
            print(f"{position}: {count}")
        
        print(f"\nRoster overlaps: {overlap_count}")
        print(f"Foreign key errors: {len(foreign_key_errors)}")

    finally:
        connection.close()

if __name__ == "__main__":
    verify_free_agents()
