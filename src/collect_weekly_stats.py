
import pandas as pd
from pathlib import Path
from src.espn_connection import connect_to_league

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "player_weekly_stats.csv"
ESPN_SEASON = 2026
POSITIONS = ["QB", "RB", "WR", "TE"]

def extract_weekly_stats(player):
    """Extract actual weekly fantasy scores for one player."""
    weekly_records = []
    stats_by_week = getattr(player, "stats", None) or {}

    for week, stats in stats_by_week.items():
        try:
            week_number = int(week)
        except (TypeError, ValueError):
            continue

        # Week 8 contains season aggregate statistics.
        if week_number <= 0:
            continue
        if not isinstance(stats, dict):
            continue

        # Missing actual points must not be treated as zero.
        points = stats.get("points")
        if points is None or pd.isna(points):
            continue

        weekly_records.append({
            "season": ESPN_SEASON,
            "player_id": player.playerId,
            "player_name": player.name,
            "week": week_number,
            "points": float(points),
        })

    return weekly_records

def collect_weekly_stats():
    """Collect weekly scores for rostered and free agent players."""
    league = connect_to_league()
    players_by_id = {}

    # Collect all rostered players.
    for team in league.teams:
        for player in team.roster:
            players_by_id[player.playerId] = player

    rostered_count = len(players_by_id)

    # Collect free agents from our existing candidate pool.
    for position in POSITIONS:
        free_agents = league.free_agents(
            size=100,
            position=position
        )
        for player in free_agents:
            players_by_id.setdefault(player.playerId, player)

    print(f"Unique rostered players: {rostered_count}")
    print(f"Total unique players: {len(players_by_id)}")

    weekly_records = []
    for player in players_by_id.values():
        weekly_records.extend(extract_weekly_stats(player))

    columns = [
        "season",
        "player_id",
        "player_name",
        "week",
        "points",
    ]

    weekly_df = pd.DataFrame(weekly_records, columns=columns)
    weekly_df = (
        weekly_df
        .drop_duplicates(subset=["season", "player_id", "week"])
        .sort_values(["player_id", "week"])
        .reset_index(drop=True)
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weekly_df.to_csv(OUTPUT_PATH, index=False)

    print("\n===== WEEKLY STATISTICS SUMMARY =====")
    print(f"Weekly records collected: {len(weekly_df)}")
    print(f"Players with weekly records: {weekly_df['player_id'].nunique()}")

    if not weekly_df.empty:
        print(f"Week range: {weekly_df['week'].min()}-{weekly_df['week'].max()}")
        print("\nSample records:")
        print(weekly_df.head(10).to_string(index=False))

    print(f"\nSaved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    collect_weekly_stats()
