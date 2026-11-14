
import sqlite3
from pathlib import Path
from src.espn_connection import connect_to_league

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"

def load_league_settings():
    # Connect to ESPN and retrieve league settings
    league = connect_to_league()
    settings = league.settings

    # Connect to SQLite database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        # Update existing league record with current settings
        cursor.execute("""
            UPDATE leagues
            SET league_name = ?,
                team_count = ?,
                scoring_type = ?,
                regular_season_weeks = ?,
                playoff_team_count = ?,
                playoff_matchup_period_length = ?,
                acquisition_budget = ?,
                faab = ?
            WHERE league_id = ?
        """,(
            settings.name.strip(),
            settings.team_count,
            settings.scoring_type,
            settings.reg_season_count,
            settings.playoff_team_count,
            settings.playoff_matchup_period_length,
            settings.acquisition_budget,
            int(settings.faab),
            league.league_id
        ))

        # Import scoring rules
        for rule in settings.scoring_format:
            cursor.execute("""
                INSERT INTO scoring_rules (
                    league_id,
                    rule_id,
                    abbreviation,
                    rule_label,
                    points
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(league_id, rule_id) DO UPDATE SET
                    abbreviation = excluded.abbreviation,
                    rule_label = excluded.rule_label,
                    points = excluded.points
            """, (
                league.league_id,
                rule["id"],
                rule["abbr"],
                rule["label"],
                rule["points"],
            ))

        # Import roster slot requirements
        for slot_name, slot_count in settings.position_slot_counts.items():
            # Skip positions that have no roster slots
            if slot_count == 0:
                continue

            cursor.execute("""
                INSERT INTO roster_slots (
                    league_id,
                    slot_name,
                    slot_count
                )
                VALUES (?, ?, ?)
                ON CONFLICT(league_id, slot_name) DO UPDATE SET
                    slot_count = excluded.slot_count
            """, (
                league.league_id,
                slot_name,
                slot_count
            ))

        connection.commit()

        # Verify imported records
        scoring_count = cursor.execute("""
            SELECT COUNT(*)
            FROM scoring_rules
            WHERE league_id = ?
        """, (league.league_id,)).fetchone()[0]

        slot_count = cursor.execute("""
            SELECT COUNT(*)
            FROM roster_slots
            WHERE league_id = ?        
        """, (league.league_id,)).fetchone()[0]

        print("League settings imported successfully!")
        print(f"Scoring rules: {scoring_count}")
        print(f"Roster slot types: {slot_count}")

        print("\nScoring Rules:")
        for rule in settings.scoring_format:
            print(
                f"{rule['label']}: {rule['points']} points"
            )
        print("\nRoster Slots:")
        for slot, count in settings.position_slot_counts.items():
            if count > 0:
                print(f"{slot}: {count}")

    finally:
        connection.close()

if __name__ == "__main__":
    load_league_settings()
