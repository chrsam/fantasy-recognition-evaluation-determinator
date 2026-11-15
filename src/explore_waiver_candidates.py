
import sqlite3
import pandas as pd
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
VOR_PATH = BASE_DIR / "data" / "vor_rankings.csv"
ESPN_SEASON = 2026
TEAM_NAME = "A Thousand Myles"

def explore_waiver_candidates():
    # Connect to database
    connection = sqlite3.connect(DATABASE_PATH) 

    try:
        # Retrieve the current roster
        roster_query = """
            SELECT
                p.player_id,
                p.player_name,
                p.position,   
                p.nfl_team,
                re.lineup_slot,
                re.average_points,
                re.injury_status   
            FROM roster_entries re
            JOIN players p
                ON re.player_id = p.player_id
            JOIN teams t
                ON re.fantasy_team_id = t.team_id
            WHERE re.season = ?
                AND t.team_name = ?
            ORDER BY p.position, re.average_points DESC
        """

        roster_df = pd.read_sql_query(
            roster_query,
            connection,
            params=(ESPN_SEASON, TEAM_NAME)
        )

        # Retrieve the latest free_agent snapshot
        free_agent_query = """
            SELECT
                p.player_id,
                p.player_name,
                p.position,   
                p.nfl_team,
                fas.average_points,
                fas.projected_avg_points,
                fas.injury_status,
                fas.percent_owned,
                fas.percent_started
            FROM free_agent_snapshots fas
            JOIN players p
                ON fas.player_id = p.player_id
            WHERE fas.season = ?
                AND fas.collected_at = (
                    SELECT MAX(collected_at)
                    FROM free_agent_snapshots
                    WHERE season = ?
                )
        """

        free_agents_df = pd.read_sql_query(
            free_agent_query,
            connection,
            params=(ESPN_SEASON, ESPN_SEASON)
        )

    finally:
        connection.close()

    # Load VOR rankings
    vor_df = pd.read_csv(VOR_PATH)

    # Attach VOR rankings to free agent records
    candidates_df = free_agents_df.merge(
        vor_df[["player_id", "vor", "position_rank"]],
        on="player_id",
        how="left"
    )

    # Identify active free agents at skill positions
    eligible_candidates = candidates_df[
        (candidates_df["injury_status"] == "ACTIVE")
        & (candidates_df["position"].isin(["QB", "RB", "WR", "TE"]))
    ].copy()

    # Identify active bench players on your roster
    bench_df = roster_df[
        (roster_df["lineup_slot"] == "BE")
        & (roster_df["injury_status"] == "ACTIVE")
        & (roster_df["position"].isin(["QB", "RB", "WR", "TE"]))
    ].copy()

    print("\n===== ACTIVE FREE AGENTS VS ACTIVE BENCH =====")
    for position in ["QB", "RB", "WR", "TE"]:

        print(f"\n--- {position} ---")

        position_bench = bench_df[
            bench_df["position"] == position
        ].sort_values("average_points")

        position_free_agents = eligible_candidates[
            eligible_candidates["position"] == position
        ].sort_values("average_points", ascending=False)

        if position_bench.empty:
            print("No active bench players at this position.")
            continue

        if position_free_agents.empty:
            print("No active free agents at this position.")
            continue

        weakest_bench = position_bench.iloc[0]
        best_free_agent = position_free_agents.iloc[0]

        improvement = (
            best_free_agent["average_points"]
            - weakest_bench["average_points"]
        )

        print(
            f"Weakest active bench player: "
            f"{weakest_bench["player_name"]}"
            f"{weakest_bench["average_points"]:.2f} PPG"
        )

        print(
            f"Best active free agent: "
            f"{best_free_agent["player_name"]}"
            f"{best_free_agent["average_points"]:.2f} PPG"
        )

        print(f"PPG difference: {improvement:+.2f}")


    # Display current roster
    print("\n===== YOUR CURRENT ROSTER =====")
    print(f"Team: {TEAM_NAME}")
    print(f"Players: {len(roster_df)}")

    print(
        roster_df[
            [
                "player_name",
                "position",
                "lineup_slot",
                "average_points",
                "injury_status"
            ]
        ].to_string(index=False)
    )

    # Display top free agent candidates
    print("\n===== TOP 20 FREE AGENTS BY VOR =====")
    top_candidates = candidates_df.sort_values(
        "vor",
        ascending=False
    ).head(20)
    print(
        top_candidates[
            [
                "player_name",
                "position",
                "average_points",
                "projected_avg_points",
                "vor",
                "percent_owned",
                "injury_status"
            ]
        ].to_string(index=False)
    )
    print("\n===== POSITION BREAKDOWN =====")
    print("\nCurrent roster:")
    print(roster_df["position"].value_counts())

    print("\nFree agents:")
    print(free_agents_df["position"].value_counts())

if __name__ == "__main__":
    explore_waiver_candidates()
