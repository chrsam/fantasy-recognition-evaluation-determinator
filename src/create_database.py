
import sqlite3
from pathlib import Path

# Locate the project and database directory
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "fantasy_league.db"

def create_database():
    # Ensure the database directory exists
    DATABASE_DIR.mkdir(exist_ok=True)

    # Connect to SQLite
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # Enable foreign key enforcement
        connection.execute("PRAGMA foreign_keys = ON")

        # Create database tables
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS leagues (
                league_id INTEGER PRIMARY KEY,
                season INTEGER NOT NULL,
                league_name TEXT,
                team_count INTEGER,
                scoring_type TEXT,
                regular_season_weeks INTEGER,
                playoff_team_count INTEGER,
                playoff_matchup_period_length INTEGER,
                acquisition_budget INTEGER,
                faab INTEGER
            );

            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY,
                league_id INTEGER NOT NULL,
                team_name TEXT NOT NULL,
                wins INTEGER,
                losses INTEGER,
                ties INTEGER,
                points_for REAL,
                points_against REAL,
                waiver_rank INTEGER,
                FOREIGN KEY (league_id) REFERENCES leagues(league_id)
            );

            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY,
                player_name TEXT NOT NULL,
                position TEXT,
                nfl_team TEXT
            );

            CREATE TABLE IF NOT EXISTS roster_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season INTEGER NOT NULL, 
                fantasy_team_id INTEGER NOT NULL, 
                player_id INTEGER NOT NULL,
                lineup_slot TEXT,
                acquisition_type TEXT,
                injury_status TEXT,
                total_points REAL,
                average_points REAL,
                projected_points REAL,
                FOREIGN KEY (fantasy_team_id) REFERENCES teams(team_id),
                FOREIGN KEY (player_id) REFERENCES players(player_id),
                UNIQUE (season, fantasy_team_id, player_id)            
            );

            CREATE TABLE IF NOT EXISTS scoring_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id INTEGER NOT NULL,
                rule_id INTEGER,
                abbreviation TEXT,
                rule_label TEXT,
                points REAL,
                FOREIGN KEY (league_id) REFERENCES leagues(league_id),
                UNIQUE (league_id, rule_id)
            );

            CREATE TABLE IF NOT EXISTS roster_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id INTEGER NOT NULL,
                slot_name TEXT NOT NULL,
                slot_count INTEGER NOT NULL,
                FOREIGN KEY (league_id) REFERENCES leagues(league_id),
                UNIQUE (league_id, slot_name)
            );
        """)

        connection.commit()

        print("Database created successfully!")
        print(f"Database location: {DATABASE_PATH}")

    finally:
        connection.close()

if __name__ == "__main__":
    create_database()
