
import sqlite3
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"

def verify_database():
    # Connect to SQLite database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        print("===== DATABASE AUDIT =====")

        # Check record counts in all six tables
        tables = [
            "leagues",
            "teams",
            "players",
            "roster_entries",
            "scoring_rules",
            "roster_slots"
        ]

        print("\nRecord Counts:")
        for table in tables:
            count = cursor.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table}: {count}")

        # Check for missing NFL team assignments
        missing_teams = cursor.execute("""
            SELECT player_name
            FROM players
            WHERE nfl_team IS NULL
        """).fetchall()

        print("\nPlayers Without NFL Teams:")
        for player in missing_teams:
            print(f"- {player[0]}")

        # Check for players assigned to multiple fantasy teams
        duplicate_ownership = cursor.execute("""
            SELECT player_id, COUNT(DISTINCT fantasy_team_id)
            FROM roster_entries
            GROUP BY player_id
            HAVING COUNT(DISTINCT fantasy_team_id) > 1
        """).fetchall()

        print(f"\nPlayers on Multiple Fantasy Teams:")
        print(len(duplicate_ownership))

        # Check roster sizes by fantasy team
        roster_sizes = cursor.execute("""
            SELECT
                teams.team_name,
                COUNT(roster_entries.player_id)
            FROM teams
            LEFT JOIN roster_entries
                ON teams.team_id = roster_entries.fantasy_team_id
            GROUP BY teams.team_id, teams.team_name
            ORDER BY teams.team_name
        """).fetchall()

        print("\nRoster Sizes:")
        for team_name, player_count in roster_sizes:
            print(f"{team_name}: {player_count} players")

        # Check foreign key relationships
        foreign_key_errors = cursor.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        print("\nForeign Key Errors:")
        print(len(foreign_key_errors))

        # Final expected-count checks
        expected_counts = {
            "leagues": 1,
            "teams": 16,
            "players": 245,
            "roster_entries": 245,
            "scoring_rules": 49,
            "roster_slots": 10
        }

        print("\nExpected Count Checks:")
        all_counts_match = True
        for table, expected in expected_counts.items():
            actual = cursor.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            passed = actual == expected
            print(
                f"{table}: "
                f"{'PASS' if passed else 'FAIL'}"
            )
            if not passed:
                all_counts_match = False

        print("\n===== AUDIT SUMMARY =====")
        if(
            all_counts_match
            and len(foreign_key_errors) == 0
            and len(duplicate_ownership) == 0
        ):
            print("Database audit passed!")
        else:
            print("Database audit requires further investigation.")

    finally:
        connection.close()

if __name__ == "__main__":
    verify_database()
    