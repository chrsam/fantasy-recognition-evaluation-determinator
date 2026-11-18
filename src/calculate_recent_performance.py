
import sqlite3
import pandas as pd
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
ESPN_SEASON = 2026

def calculate_recent_performance():
    """Calculate recent fantasy production for each player."""

    # Connect to SQLite database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        query = """
            SELECT
                p.player_id,
                p.player_name,
                p.position,
                w.week,
                w.points
            FROM player_weekly_stats AS w
            JOIN players AS p
                ON w.player_id = p.player_id
            WHERE w.season = ?
            ORDER BY p.player_id, w.week DESC
        """

        weekly_df = pd.read_sql_query(
            query,
            connection,
            params=(ESPN_SEASON,)
        )

    finally:
        connection.close()

    if weekly_df.empty:
        print("No weekly statistics available.")
        return pd.DataFrame()

    # Most recent recorded scores appear first.
    weekly_df = weekly_df.sort_values(
        ["player_id", "week"],
        ascending=[True, False]
    )

    grouped = weekly_df.groupby("player_id")

    recent_df = grouped.agg(
        player_name=("player_name", "first"),
        position=("position", "first"),
        games_recorded=("points", "count"),
        latest_recorded_week=("week", "max"),
    ).reset_index()

    last_3 = (
        weekly_df.groupby("player_id")
        .head(3)
        .groupby("player_id")["points"]
        .mean()
    )

    last_5 = (
        weekly_df.groupby("player_id")
        .head(5)
        .groupby("player_id")["points"]
        .mean()
    )

    recent_df["last_3_ppg"] = (
        recent_df["player_id"].map(last_3)
    )

    recent_df["last_5_ppg"] = (
        recent_df["player_id"].map(last_5)
    )

    # Require sufficient recorded games.
    recent_df.loc[
        recent_df["games_recorded"] < 3,
        "last_3_ppg"
    ] = float("nan")

    recent_df.loc[
        recent_df["games_recorded"] < 5,
        "last_5_ppg"
    ] = float("nan")

    # Season average from recorded weekly scores.
    season_ppg = grouped["points"].mean()

    recent_df["season_ppg"] = (
        recent_df["player_id"].map(season_ppg)
    )

    # Recent production relative to season average.
    recent_df["recent_vs_season"] = (
        recent_df["last_3_ppg"] - recent_df["season_ppg"]
    )

    # Determine the latest week w/ recorded actual scores.
    latest_available_week = int(weekly_df["week"].max())

    # Count how many weeks have passed since each player's 
    # most recent recorded fantasy score.
    recent_df["weeks_since_last_game"] = (
        latest_available_week
        - recent_df["latest_recorded_week"]
    )

    # Flag players w/ older performance data.
    recent_df["performance_freshness"] = (
        recent_df["weeks_since_last_game"].apply(
            lambda weeks: (
                "CURRENT" if weeks == 0
                else "ONE WEEK OLD" if weeks == 1
                else "STALE"
            )
        )
    )

    return recent_df

def main():

    recent_df = calculate_recent_performance()
    if recent_df.empty:
        return

    print("\n===== RECENT PLAYER PERFORMANCE =====")
    print(f"Players analyzed: {len(recent_df)}")
    print("\nTop 15 players by last 3 games PPG:")

    top_players = (
        recent_df
        .dropna(subset=["last_3_ppg"])
        .sort_values(
            ["weeks_since_last_game", "last_3_ppg"], 
            ascending=[True, False]
        )
        .head(15)
    )

    print(
        top_players[
            [
                "player_name",
                "position",
                "games_recorded",
                "latest_recorded_week",
                "weeks_since_last_game",
                "performance_freshness",
                "season_ppg",
                "last_3_ppg",
                "last_5_ppg",
                "recent_vs_season",
            ]
        ].round(2).to_string(index=False)
    )

if __name__ == "__main__":
    main()
