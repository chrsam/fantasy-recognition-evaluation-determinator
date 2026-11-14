
import pandas as pd

def validate_teams():
    teams_df = pd.read_csv("data/teams.csv")

    print("\n===== TEAM DATA VALIDATION =====")

    print(f"Number of teams: {len(teams_df)}")
    print(f"Duplicate team IDs: {teams_df['team_id'].duplicated().sum()}")
    print(f"Missing values:\n{teams_df.isnull().sum()}")

    print("\nTeam records:")
    print(teams_df[["team_name", "wins", "losses", "points_for"]])

def validate_rosters():
    rosters_df = pd.read_csv("data/rosters.csv")

    print("\n===== ROSTER DATA VALIDATION =====")

    print(f"Total players: {len(rosters_df)}")
    print(f"Unique players: {rosters_df['player_id'].nunique()}")
    print(f"Duplicate player IDs: {rosters_df['player_id'].duplicated().sum()}")

    print(f"\nMissing values:")
    print(rosters_df.isnull().sum())

    print("\nFree agents:")
    missing_nfl_team = rosters_df[
        rosters_df["nfl_team"].isnull()
    ]

    print(
        missing_nfl_team[
            ["player_name", "position", "fantasy_team_name"]
        ]
    )

    print("\nPlayers by fantasy team:")
    print(
        rosters_df.groupby("fantasy_team_name")["player_id"]
        .count()
        .sort_values(ascending=False)
    )

    print("\nPlayers by position")
    print(rosters_df["position"].value_counts(dropna=False))

    print("\nInjury status distribution:")
    print(rosters_df["injury_status"].value_counts(dropna=False))

def main():
    validate_teams()
    validate_rosters()

if __name__ == "__main__":
    main()
