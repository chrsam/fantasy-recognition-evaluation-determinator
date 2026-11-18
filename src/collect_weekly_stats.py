
import pandas as pd
from pathlib import Path
from src.espn_connection import connect_to_league

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "player_weekly_stats.csv"
ESPN_SEASON = 2026
POSITIONS = ["QB", "RB", "WR", "TE"]
BATCH_SIZE = 10

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

    player_ids = list(players_by_id.keys())

    total_batches = (
        len(player_ids) + BATCH_SIZE - 1
    ) // BATCH_SIZE

    for start in range(0, len(player_ids), BATCH_SIZE):
        batch_ids = player_ids[start:start + BATCH_SIZE]
        batch_number = start // BATCH_SIZE + 1

        print(
            f"Retrieving batch {batch_number}/{total_batches} "
            f"{len(batch_ids)} players"
        )

        try:
            detailed_players = league.player_info(
                playerId=batch_ids
            )

            if not isinstance(detailed_players, list):
                detailed_players = [detailed_players]

            returned_ids = {
                player.playerId for player in detailed_players
            }

            missing_ids = set(batch_ids) - returned_ids

            if missing_ids:
                raise ValueError(
                    f"Batch {batch_number} returned incomplete data. "
                    f"Missing player IDs: {sorted(missing_ids)}"
                )

            for player in detailed_players:
                weekly_records.extend(
                    extract_weekly_stats(player)
                )

        except Exception as error:
            print(
                f"ERROR retrieving batch {batch_number}: {error}"
            )
            raise

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
