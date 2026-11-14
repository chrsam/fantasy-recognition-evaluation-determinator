
import sqlite3
import pandas as pd
from pathlib import Path

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "fantasy_league.db"

def calculate_vor():
    # Connect to SQLite database
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # Retrieve player stats
        query = """
            SELECT
                players.player_id,
                players.player_name,
                players.position,
                teams.team_name AS fantasy_team,
                roster_entries.average_points
            FROM players
            JOIN roster_entries
                ON players.player_id = roster_entries.player_id
            JOIN teams
                ON roster_entries.fantasy_team_id = teams.team_id
        """

        df = pd.read_sql_query(query, connection)

        # Convert average points to numeric values
        df["average_points"] = pd.to_numeric(
            df["average_points"],
            errors="coerce"
        )

        # Exclude players without average points 
        df = df.dropna(
            subset=["average_points", "position"]
        ).copy()

        print("===== PLAYER DATA LOADED =====")
        print(f"Players available for analysis: {len(df)}")

        print("\nPlayers by position:")
        print(df["position"].value_counts().to_string())

        # Separate RB, WR, and TE players for flex analysis
        flex_df = df[
            df["position"].isin(["RB", "WR", "TE"])
        ].copy()

        # Fill dedicated starting positions
        dedicated_starters = {
            "RB": 16,
            "WR": 32,
            "TE": 16
        }

        remaining_players = flex_df.copy()
        starter_counts = dedicated_starters.copy() 

        for position, starter_count in dedicated_starters.items():
            position_players = remaining_players[
                remaining_players["position"] == position
            ].sort_values(
                "average_points",
                ascending=False
            )
            remaining_players = remaining_players.drop(
                position_players.head(starter_count).index
            )

        # Allocate 16 RB/WR flex positions
        rb_wr_candidates = remaining_players[
            remaining_players["position"].isin(["RB", "WR"])
        ].sort_values(
            "average_points",
            ascending=False
        )

        rb_wr_flex = rb_wr_candidates.head(16)

        for position, count in rb_wr_flex["position"].value_counts().items():
            starter_counts[position] += count

        remaining_players = remaining_players.drop(
            rb_wr_flex.index
        )

        # Allocate 16/RB/WR/TE flex positions
        flex_candidates = remaining_players.sort_values(
            "average_points",
            ascending=False
        )

        rb_wr_te_flex = flex_candidates.head(16)

        for position, count in rb_wr_te_flex["position"].value_counts().items():
            starter_counts[position] += count        

        # Display starting position allocations
        print("\n===== FLEX POSITION ALLOCATION =====")

        for position in ["RB", "WR", "TE"]:
            print(
                f"{position}: {starter_counts[position]} "
                "starting opportunities"
            )

        print("\nRB/WR flex allocation:")
        print(
            rb_wr_flex["position"].value_counts().to_string()
        )

        print("\nRB/WR/TE flex allocation:")
        print(
            rb_wr_te_flex["position"].value_counts().to_string()
        )

        # Define provisional replacement-level ranks
        replacement_ranks = {
            "QB": 17,
            "RB": starter_counts["RB"] + 1,
            "WR": starter_counts["WR"] + 1,
            "TE": starter_counts["TE"] + 1
        }

        # Calculate replacement-level point by position
        replacement_points = {}
        for position, replacement_rank in replacement_ranks.items():
            position_df = df[
                df["position"] == position
            ].sort_values(
                "average_points",
                ascending=False
            )

            if len(position_df) >= replacement_rank:
                replacement_player = position_df.iloc[
                    replacement_rank - 1
                ]
                replacement_points[position] = (
                    replacement_player["average_points"]
                )
                print(
                    f"\n{position} replacement level "
                    f"(rank {replacement_rank}): "
                    f"{replacement_player['player_name']} - "
                    f"{replacement_player['average_points']:.2f} PPG"
                )
            else:
                print(
                    f"\nNot enough {position} players "
                    "to establish replacement level."
                )

        # Assign replacement-level points to each player
        df["replacement_points"] = df["position"].map(
            replacement_points
        )

        # Calculate Value Over Replacement (VOR)
        df["vor"] = (
            df["average_points"] - df["replacement_points"]
        )

        # Exclude positions without a replacement baseline
        vor_df = df.dropna(
            subset=["replacement_points"]
        ).copy()

        # Display top 10 players at each position by VOR
        print("\n===== TOP 10 PLAYERS BY POSITIONAL VOR =====")
        for position in sorted(vor_df["position"].unique()):
            position_df = vor_df[
                vor_df["position"] == position
            ].sort_values(
                ["vor", "player_name"],
                ascending=[False, True]
            )
            print(f"\n--- {position} ---")
            print(
                position_df[
                    [
                        "player_name",
                        "average_points",
                        "replacement_points",
                        "vor"
                    ]
                ].head(10).to_string(
                    index=False,
                    formatters={
                        "average_points": "{:.2f}".format,
                        "replacement_points": "{:.2f}".format,
                        "vor": "{:.2f}".format,
                    }
                )
            )

        # Display top 20 players overall by VOR
        print("\n===== TOP 20 PLAYERS OVERALL BY VOR =====")
        overall_vor = vor_df.sort_values(
            ["vor", "player_name"],
            ascending=[False, True]
        )
        print(
            overall_vor[
                [
                    "player_name",
                    "position",
                    "average_points",
                    "replacement_points",
                    "vor"        
                ]
            ].head(20).to_string(
                index=False,
                formatters={
                    "average_points": "{:.2f}".format,
                    "replacement_points": "{:.2f}".format,
                    "vor": "{:.2f}".format,
                }
            )
        )

    finally:
        connection.close()

if __name__ == "__main__":
    calculate_vor()
