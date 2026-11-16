
import sqlite3
import pandas as pd
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"
VOR_PATH = BASE_DIR / "data" / "vor_rankings.csv"

ESPN_SEASON = 2026
TEAM_NAME = "A Thousand Myles"
POSITIONS = ["QB", "RB", "WR", "TE"]
INJURY_STATUSES = [
    "QUESTIONABLE",
    "DOUBTFUL",
    "OUT",
    "INJURY_RESERVE"
]

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
                re.projected_avg_points,
                re.projected_total_points,
                re.injury_status,
                re.active_status   
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
                fas.projected_total_points,
                fas.injury_status,
                fas.active_status,
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

    # Attach VOR rankings to current roster players
    roster_df = roster_df.merge(
        vor_df[["player_id", "vor", "position_rank"]],
        on="player_id",
        how="left"
    )

    for df in [roster_df, free_agents_df]:
        df["injury_status"] = (
            df["injury_status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df["active_status"] = (
            df["active_status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

    roster_df["lineup_slot"] = (
        roster_df["lineup_slot"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Attach VOR rankings to free agent records
    candidates_df = free_agents_df.merge(
        vor_df[["player_id", "vor", "position_rank"]],
        on="player_id",
        how="left"
    )

    # Verify VOR coverage for rostered skill-position players
    skill_roster_df = roster_df[
        roster_df["position"].isin(POSITIONS)
    ]
    missing_vor = skill_roster_df["vor"].isna()

    print("\n===== ROSTER VOR VALIDATION =====")
    print(f"Skill-position players: {len(skill_roster_df)}")
    print(f"Players with VOR: {len(skill_roster_df) - missing_vor.sum()}")
    print(f"Players missing VOR: {missing_vor.sum()}")

    if missing_vor.any():
        print("\nPlayers missing VOR:")
        print(
            skill_roster_df.loc[
                missing_vor,
                ["player_name", position]
            ].to_string(index=False)
        )

    print("\n===== FILTER DIAGNOSTICS =====")

    print("\nRoster lineup slots:")
    print(roster_df["lineup_slot"].value_counts(dropna=False))

    print("\nRoster injury statuses:")
    print(roster_df["injury_status"].value_counts(dropna=False))

    print("\nRoster activity statuses:")
    print(roster_df["active_status"].value_counts(dropna=False))

    print("\nFree-agent injury statuses:")
    print(free_agents_df["injury_status"].value_counts(dropna=False))

    print("\nFree-agent activity statuses:")
    print(free_agents_df["active_status"].value_counts(dropna=False))

    # Immediate pickup candidates
    # Identify active, healthy free agents at skill positions
    eligible_candidates = candidates_df[
        (candidates_df["injury_status"] == "ACTIVE")
        & (candidates_df["active_status"] == "active") 
        & (candidates_df["position"].isin(POSITIONS))
    ].copy()

    # Identify active bench players on your roster
    bench_df = roster_df[
        (roster_df["lineup_slot"] == "BE")
        & (roster_df["injury_status"] == "ACTIVE")
        & (roster_df["active_status"] == "active")
        & (roster_df["position"].isin(POSITIONS))
    ].copy()

    # Compare every eligible free agent against the weakest
    # active bench player at the same position
    recommendation_rows = []
    for position in POSITIONS:
        position_bench = bench_df[
            bench_df["position"] == position
        ].sort_values("average_points")

        position_free_agents = eligible_candidates[
            eligible_candidates["position"] == position
        ].copy()

        # Skip positons without an active bench player
        if position_bench.empty:
            continue

        weakest_bench = position_bench.iloc[0]

        for _, candidate in position_free_agents.iterrows():
            actual_difference = (
                candidate["average_points"]
                - weakest_bench["average_points"]
            )

            # Only compare projections when both are available
            projected_difference = float("nan")

            if(
                candidate["projected_avg_points"] > 0
                and weakest_bench["projected_avg_points"] > 0
            ):
                projected_difference = (
                    candidate["projected_avg_points"]
                    - weakest_bench["projected_avg_points"]
                )

            recommendation_rows.append({
                "position": position,
                "free_agent": candidate["player_name"],
                "bench_player": weakest_bench["player_name"],
                "free_agent_ppg": candidate["average_points"],
                "bench_ppg": weakest_bench["average_points"],
                "actual_ppg_difference": actual_difference,
                "projected_ppg_difference": projected_difference,
                "vor": candidate["vor"],
                "percent_owned": candidate["percent_owned"]
            })

    recommendations_df = pd.DataFrame(recommendation_rows)

    print("\n==== POTENTIAL BENCH UPGRADES =====")
    if recommendations_df.empty:
        print("No position comparisions available.")
    else:
        recommendations_df = recommendations_df.sort_values(
            "actual_ppg_difference",
            ascending=False
        )

        print(
            recommendations_df[
                [
                    "position",
                    "free_agent",
                    "bench_player",
                    "free_agent_ppg",
                    "bench_ppg",
                    "actual_ppg_difference",
                    "projected_ppg_difference",
                    "vor"
                ]
            ].to_string(index=False)
        )

    # Starter slots eligible for each position
    # Flex players are included wherever their slot allows them to play.
    starter_slots = {
        "QB": ["QB"],
        "RB": ["RB", "RB/WR", "RB/WR/TE"],
        "WR": ["WR", "RB/WR", "RB/WR/TE"],
        "TE": ["TE", "RB/WR/TE"]
    }

    starter_recommendation_rows = []

    for position in POSITIONS:
        # Find current starters eligible at this position.
        position_starters =roster_df[
            (roster_df["lineup_slot"].isin(starter_slots[position]))
            & (roster_df["position"] == position)
        ].copy()

        # Find eligible free agents at this position
        position_free_agents = eligible_candidates[
            eligible_candidates["position"] == position
        ].copy()

        if position_starters.empty or position_free_agents.empty:
            continue

        # Identify the lowest-scoring starter at this position
        weakest_starter = position_starters.sort_values(
            "average_points"
        ).iloc[0]

        for _, candidate in position_free_agents.iterrows():
            actual_difference = (
                candidate["average_points"]
                - weakest_starter["average_points"]
            )

            # Compare projections only when both are available
            projected_difference = float("nan")

            candidate_projection = candidate["projected_avg_points"]
            starter_projection = weakest_starter["projected_avg_points"]

            if (
                pd.notna(candidate_projection)
                and pd.notna(starter_projection)
                and candidate_projection > 0
                and starter_projection > 0
            ):
                projected_difference = (
                    candidate_projection - starter_projection
                )

            starter_recommendation_rows.append({
                "position": position,
                "free_agent": candidate["player_name"],
                "weakest_starter": weakest_starter["player_name"],
                "starter_injury_status": weakest_starter["injury_status"],
                "free_agent_ppg": candidate["average_points"],
                "starter_ppg": weakest_starter["average_points"],
                "actual_ppg_difference": actual_difference,
                "projected_ppg_difference": projected_difference,
                "vor": candidate["vor"]
            })

    starter_recommendations_df = pd.DataFrame(
        starter_recommendation_rows
    )

    print("\n===== POTENTIAL STARTER UPGRADES =====")
    if starter_recommendations_df.empty:
        print("No starter comparisons available.")
    else:
        starter_recommendations_df = starter_recommendations_df.sort_values(
            "actual_ppg_difference",
            ascending=False
        )
        for position in POSITIONS:
            position_results = starter_recommendations_df[
                starter_recommendations_df["position"] == position
            ].head(5)
            print(f"\n--- {position} ---")
            if position_results.empty:
                print("No comparisons available.")
                continue
            print(
                position_results[
                    [
                        "free_agent",
                        "weakest_starter",
                        "starter_injury_status",
                        "free_agent_ppg",
                        "starter_ppg",
                        "actual_ppg_difference",
                        "projected_ppg_difference",
                        "vor"
                    ]
                ].to_string(index=False)
            )

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
                "projected_avg_points",
                "injury_status",
                "active_status"
            ]
        ].to_string(index=False)
    )

    print("\n===== FREE AGENTS VS ACTIVE BENCH =====")
    for position in POSITIONS:

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

        actual_difference = (
            best_free_agent["average_points"]
            - weakest_bench["average_points"]
        )

        candidate_projection = best_free_agent["projected_avg_points"]
        bench_projection = weakest_bench["projected_avg_points"]
        projected_difference = None

        if (
            pd.notna(candidate_projection)
            and pd.notna(bench_projection)
            and candidate_projection > 0
            and bench_projection > 0
        ):
            projected_difference = candidate_projection - bench_projection

        print(
            f"Weakest active bench player: {weakest_bench['player_name']}"
        )
        print(f"Actual PPG: {weakest_bench['average_points']:.2f}")
        print(f"Projected PPG: {weakest_bench['projected_avg_points']:.2f}")
        print()
        print(
            f"Best free agent by VOR: {best_free_agent['player_name']}"
        )
        print(f"Actual PPG: {best_free_agent["average_points"]:.2f}")
        print(f"Projected PPG: {best_free_agent['projected_avg_points']:.2f}")
        print(f"VOR: {best_free_agent['vor']:.2f}")
        print(f"Actual PPG difference: {actual_difference:+.2f}")
        if projected_difference is not None:
            print(f"Projected PPG difference: {projected_difference:+.2f}")
        else:
            print("Projected PPG difference: Unavailable")

    # Display top free agent candidates
    print("\n===== TOP 20 ELIGIBLE FREE AGENTS BY VOR =====")

    top_candidates = eligible_candidates.sort_values(
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

    # Display injured/questionable free agents separately
    injured_candidates = candidates_df[
        (candidates_df["injury_status"].isin(INJURY_STATUSES))
        & (candidates_df["position"].isin(POSITIONS))
    ].copy()

    print("\n===== FREE AGENTS WITH INJURY DESIGNATIONS =====")

    print(
        injured_candidates[
            [
                "player_name",
                "position",
                "average_points",
                "projected_avg_points",
                "vor",
                "percent_owned",
                "injury_status"
            ]
        ]
        .sort_values("vor", ascending=False)
        .head(20)
        .to_string(index=False)
    )

    print("\n===== POSITION BREAKDOWN =====")
    print("\nCurrent roster:")
    print(roster_df["position"].value_counts())

    print("\nFree agents collected:")
    print(free_agents_df["position"].value_counts())

    print("\nEligible immediate pickup candidates:")
    print(eligible_candidates["position"].value_counts())

if __name__ == "__main__":
    explore_waiver_candidates()
