
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
POSITION_TARGETS = {
    "QB": 2,
    "RB": 4,
    "WR": 4,
    "TE": 2,
}
POSITION_WEIGHTS = {
    "QB": 1.0,
    "RB": 1.5,
    "WR": 2.0,
    "TE": 1.0,
}
MINIMUM_DEPTH = {
    "QB": 1,
    "RB": 3,
    "WR": 2,
    "TE": 1,
}
STRONG_VOR_THRESHOLD = 2.0
CONSIDER_VOR_THRESHOLD = 0.5

def classify_transaction(row):
    drop_position = row["drop_position"]
    minimum_depth = MINIMUM_DEPTH.get(drop_position, 1)
    depth_is_acceptable = (
        row["post_drop_depth"] >= minimum_depth
    )
    production_improves = (
        pd.notna(row["actual_ppg_difference"])
        and row["actual_ppg_difference"] >= 0
    )
    value_improves = row["vor_improvement"]
    weighted_gap_improvement = (
        row["weighted_gap_improvement"]
    )

    # Reject transactions that leave insufficient depth
    if not depth_is_acceptable:
        return "LOW PRIORITY"

    # Strong candidate: improves player value and production
    if (
        value_improves >= STRONG_VOR_THRESHOLD
        and production_improves
        and weighted_gap_improvement >= 0
    ):
        return "STRONG CANDIDATE"

    # Worth considering: positive player value and production
    # w/ no major positional depth problem
    if (
        value_improves >= CONSIDER_VOR_THRESHOLD
        and production_improves
        and weighted_gap_improvement >= 0
    ):
        return "WORTH CONSIDERING"

    return "LOW PRIORITY"

def explain_transaction(row):
    pickup = row["pickup"]
    drop = row["drop"]

    pickup_position = row["pickup_position"]
    drop_position = row["drop_position"]

    vor_difference = row["vor_improvement"]
    ppg_difference = row["actual_ppg_difference"]
    projected_difference = row["projected_ppg_difference"]

    explanation = []

    # Player value
    explanation.append(
        f"{pickup} improves VOR by {vor_difference:+.2f} "
        f"compared to {drop}."
    )

    # Historical production
    explanation.append(
        f"Historical production changes by "
        f"{ppg_difference:+.2f} PPG."
    )

    # Positional impact
    if pickup_position != drop_position:
        post_drop_depth = row["post_drop_depth"]
        target_depth = POSITION_TARGETS[drop_position]

        explanation.append(
            f"Adds {pickup_position} depth but reduces "
            f"{drop_position} depth to {post_drop_depth} "
            f"(target: {target_depth})."
        )
    else:
        explanation.append(
            f"Maintains {drop_position} positional depth "
            f"at {row['post_drop_depth']} players."
        )

    # Projection comparison
    if pd.notna(projected_difference):
        if projected_difference > 0:
            explanation.append(
                f"Projection supports the move "
                f"({projected_difference:+.2f} PPG)."
            )
        elif projected_difference < 0:
            explanation.append(
                f"Projection conflicts with historical results "
                f"({projected_difference:+.2f} PPG)."
            )
        else:
            explanation.append(
                "Projected production is approximately equal."
            )
    else:
        explanation.append(
            "Projection comparison is unavailable."
        )

    return " ".join(explanation)

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

    # Count healthy, active players at each skill position.
    # Injured, inactive, and IR players do not count towards
    # our usable positional depth.
    usable_roster_df = roster_df[
        (roster_df["active_status"] == "active") 
        & (roster_df["injury_status"] == "ACTIVE")
        & (roster_df["lineup_slot"] != "IR")
        & (roster_df["position"].isin(POSITION_TARGETS))
    ].copy()

    position_counts = (
        usable_roster_df["position"]
        .value_counts()
        .to_dict()
    )

    position_gaps = {}

    for position, target in POSITION_TARGETS.items():
        current_count = position_counts.get(position, 0)
        position_gaps[position] = max(
            target - current_count,
            0
        )

    print("\n===== CURRENT POSITIONAL NEEDS =====")
    for position, target in POSITION_TARGETS.items():
        current_count = position_counts.get(position, 0)
        gap = position_gaps[position]

        print(
            f"{position}: {current_count}/{target} "
            f"| Players needed: {gap}"
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

    # Identify potential add/drop transactions.
    # Compare each eligible free agent against every healthy
    # active bench player, regardless of position.
    transaction_rows = []
    for _, candidate in eligible_candidates.iterrows():
        for _, drop_player in bench_df.iterrows():
            # Calculate the diference in VOR.
            vor_improvement = (
                candidate["vor"] - drop_player["vor"]
            ) 

            # Calculate historical scoring difference
            actual_difference = (
                candidate["average_points"]
                - drop_player["average_points"]
            )

            # Compare projections only when both are available.
            projected_difference = float("nan")

            candidate_projection = candidate["projected_avg_points"]
            drop_projection = drop_player["projected_avg_points"]

            if (
                pd.notna(candidate_projection)
                and pd.notna(drop_projection)
                and candidate_projection > 0
                and drop_projection > 0
            ):
                projected_difference = (
                    candidate_projection - drop_projection
                )

            # Determine whether the pickup address a
            # positional depth shortage
            pickup_position = candidate["position"]
            position_need_gap = position_gaps.get(
                pickup_position, 0
            )
            if position_need_gap >= 2:
                position_need = "HIGH"
                position_need_rank = 1
            elif position_need_gap == 1:
                position_need = "MODERATE"
                position_need_rank = 2
            else:
                position_need = "LOW"
                position_need_rank = 3

            # Calculate positional depth after the transaction.
            post_transaction_counts = position_counts.copy()

            # Remove the dropped player's position.
            post_transaction_counts[drop_player["position"]] = (
                post_transaction_counts.get(
                    drop_player["position"], 0
                ) - 1
            )

            # Add the pickup's position.
            post_transaction_counts[pickup_position] = (
                post_transaction_counts.get(
                    pickup_position, 0
                ) + 1
            )

            # Identify whether the transaction leaves a position empty.
            positions_below_minimum = [
                position
                for position, count in post_transaction_counts.items()
                if count < 1
            ]

            # Calculate remaining positional shortages.
            remaining_gaps = {}
            for position, target in POSITION_TARGETS.items():
                current_count = post_transaction_counts.get(
                    position, 0
                )
                remaining_gaps[position] = max(
                    target - current_count,
                    0
                )

            current_weighted_gap = sum(
                position_gaps[position] * POSITION_WEIGHTS[position]
                for position in POSITION_TARGETS
            )
            post_weighted_gap = sum(
                remaining_gaps[position] * POSITION_WEIGHTS[position]
                for position in POSITION_TARGETS
            )
            weighted_gap_improvement = (
                current_weighted_gap - post_weighted_gap
            )

            total_remaining_gaps = sum(
                remaining_gaps.values()
            )
            total_current_gaps = sum(position_gaps.values())
            positional_gap_improvement = (
                total_current_gaps - total_remaining_gaps
            )

            new_position_gaps = [
                position
                for position in POSITION_TARGETS
                if remaining_gaps[position] > position_gaps[position]
            ]

            transaction_rows.append({
                "pickup": candidate["player_name"],
                "pickup_position": candidate["position"],
                "drop": drop_player["player_name"],
                "drop_position": drop_player["position"],
                "pickup_vor": candidate["vor"],
                "drop_vor": drop_player["vor"],
                "vor_improvement": vor_improvement,
                "actual_ppg_difference": actual_difference,
                "projected_ppg_difference": projected_difference,  
                "position_need": position_need,
                "position_need_gap": position_need_gap,
                "position_need_rank": position_need_rank, 
                "post_pickup_depth": post_transaction_counts.get(
                    pickup_position, 0
                ),  
                "post_drop_depth": post_transaction_counts.get(
                    drop_player["position"], 0
                ),  
                "positional_gap_improvement": positional_gap_improvement,
                "total_remaining_gaps": total_remaining_gaps,
                "weighted_gap_improvement": weighted_gap_improvement,
                "positions_below_minimum": positions_below_minimum,
                "new_position_gaps": new_position_gaps,
            })

    transactions_df = pd.DataFrame(transaction_rows)

    # Part A: apply classifications
    transactions_df["recommendation"] = (
        transactions_df.apply(
            classify_transaction,
            axis=1
        )
    )

    transactions_df["explanation"] = (
        transactions_df.apply(
            explain_transaction,
            axis=1
        )
    )

    RECOMMENDATION_ORDER = {
        "STRONG CANDIDATE": 1,
        "WORTH CONSIDERING": 2,
        "LOW PRIORITY": 3
    }

    transactions_df["recommendation_rank"] = (
        transactions_df["recommendation"]
        .map(RECOMMENDATION_ORDER)
    )

    # Keep only transactions that improve VOR.
    if not transactions_df.empty:
        transactions_df = transactions_df[
            transactions_df["vor_improvement"] > 0
        ].copy()

    # Validate positional minimum depth safeguard
    invalid_depth_transacations = transactions_df[
        transactions_df["positions_below_minimum"].apply(
            lambda positions: len(positions) > 0
        )
    ]

    print("\n===== POSITIONAL DEPTH VALIDATION =====")
    print(
        f"Transactions evaluated: {len(transactions_df)}"
    )
    print(
        f"Transactions violating minimum depth: "
        f"{len(invalid_depth_transacations)}"
    )

    if invalid_depth_transacations.empty:
        print("PASS: No transactions violate minimum positional depth.")
    else:
        print("WARNING: Some transactions violate minimum positional depth.")
        print(
            invalid_depth_transacations[
                ["pickup", "drop", "positions_below_minimum"]
            ].to_string(index=False)
        )

    # Print recommendation summary
    print("\n===== RECOMMENDATION SUMMARY =====")
    if not transactions_df.empty:
        print(
            transactions_df["recommendation"]
            .value_counts()
            .to_string()
        )
    else:
        print("No positive-VOR transactions found.")

    # Sort transactions
    transactions_df = transactions_df.sort_values(
        by=[
            "recommendation_rank",
            "weighted_gap_improvement",
            "vor_improvement"
        ],
        ascending=[
            True,
            False,
            False
        ]
    )

    print("\n===== TOP POTENTIAL ADD/DROP TRANSACTIONS =====")
    print(f"Positive-VOR transactions: {len(transactions_df)}")
    if not transactions_df.empty:
        display_columns = [
            "recommendation",
            "pickup",
            "pickup_position",
            "drop",
            "drop_position",
            "positional_gap_improvement",
            "total_remaining_gaps",
            "weighted_gap_improvement",
            "positions_below_minimum",
            "new_position_gaps",
            "vor_improvement",
            "actual_ppg_difference",
            "projected_ppg_difference",
            "explanation"
        ]

        print(
            transactions_df[display_columns]
            .head(15)
            .to_string(index=False)
        )

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
