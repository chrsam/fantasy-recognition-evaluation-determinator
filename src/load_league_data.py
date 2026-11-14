
import sqlite3
import pandas as pd
from pathlib import Path

# Locate project files
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
TEAMS_CSV_PATH = BASE_DIR / "data" / "teams.csv"

# League configuration
ESPN_LEAGUE_ID=319030083
ESPN_SEASON=2026

def load_league_data():
    # Read team information
    teams_df = pd.read_csv(TEAMS_CSV_PATH)

    # Connect to database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        # Insert league information
        cursor.execute("""
            INSERT INTO leagues (
                league_id,
                season,
                league_name,
                team_count,
                scoring_type,
                regular_season_weeks,
                playoff_team_count,
                playoff_matchup_period_length,
                acquisition_budget,
                faab
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(league_id) DO UPDATE SET
                season = excluded.season,
                league_name = excluded.league_name,
                team_count = excluded.team_count,
                scoring_type = excluded.scoring_type,
                regular_season_weeks = excluded.regular_season_weeks,
                playoff_team_count = excluded.playoff_team_count,
                playoff_matchup_period_length = excluded.playoff_matchup_period_length,
                acquisition_budget = excluded.acquisition_budget,
                faab = excluded.faab

        """, (
            ESPN_LEAGUE_ID,
            ESPN_SEASON,
            "PTV Fantasy Football",
            16,
            "H2H_POINTS",
            14,
            8,
            1,
            100,
            0
        ))

        # Insert team information
        for _, team in teams_df.iterrows():
            cursor.execute("""
                INSERT INTO teams (
                    team_id,
                    league_id,
                    team_name,
                    wins,
                    losses,
                    ties,
                    points_for, 
                    points_against,
                    waiver_rank
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(team_id) DO UPDATE SET
                    league_id = excluded.league_id,
                    team_name = excluded.team_name,
                    wins = excluded.wins,
                    losses = excluded.losses,
                    ties = excluded.ties,
                    points_for = excluded.points_for, 
                    points_against = excluded.points_against,
                    waiver_rank = excluded.waiver_rank

            """, (
                int(team["team_id"]),
                ESPN_LEAGUE_ID,
                team["team_name"],
                int(team["wins"]),
                int(team["losses"]),
                int(team["ties"]),
                float(team["points_for"]),
                float(team["points_against"]),
                int(team["waiver_rank"])
            ))

        connection.commit()

        # Verify imported records
        league_count = cursor.execute(
            "SELECT COUNT(*) FROM leagues"
        ).fetchone()[0]

        team_count = cursor.execute(
            "SELECT COUNT(*) FROM teams"
        ).fetchone()[0]

        print("League and team data imported successfully!")
        print(f"Leagues in database: {league_count}")
        print(f"Teams in database: {team_count}")

    finally:
        connection.close()

if __name__ == "__main__":
    load_league_data()
