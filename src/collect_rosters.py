
import pandas as pd

from src.espn_connection import connect_to_league

def collect_team_data(league):
    """Collect basic information about every fantasy team."""

    teams_data = []

    for team in league.teams:
        team_record = {
            "team_id": team.team_id,
            "team_name": team.team_name,
            "wins": team.wins,
            "losses": team.losses,
            "ties": team.ties,
            "points_for": team.points_for,
            "points_against": team.points_against,
            "waiver_rank": team.waiver_rank,
        }

        teams_data.append(team_record)

    return pd.DataFrame(teams_data)

def collect_roster_data(league):
    """Collect player info from every fantasy team."""

    roster_data = []

    for team in league.teams:
        for player in team.roster:
            player_record = {
                "fantasy_team_id": team.team_id,
                "fantasy_team_name": team.team_name,
                "player_id": player.playerId,
                "player_name": player.name,
                "position": player.position,
                "nfl_team": player.proTeam,
                "lineup_slot": player.lineupSlot,
                "acquisition_type": player.acquisitionType,
                "injury_status": player.injuryStatus,
                "total_points": player.total_points,
                "average_points": player.avg_points,
                "projected_points": player.projected_total_points,
            }

            roster_data.append(player_record)

    return pd.DataFrame(roster_data)

def main():
    print("Connecting to ESPN...")
    league = connect_to_league()

    print("Collecting team information...")
    teams_df = collect_team_data(league)

    print("Collecting player rosters...")
    rosters_df = collect_roster_data(league)

    # Save data locally
    teams_df.to_csv("data/teams.csv", index=False)
    rosters_df.to_csv("data/rosters.csv", index=False)

    print("\nCollection complete!")
    print("======================")

    print(f"Teams collected: {len(teams_df)}")
    print(f"Players collected: {len(rosters_df)}")

    print("\nTeam Data Preview:")
    print(teams_df.head())

    print("\nRoster Data Preview:")
    print(rosters_df.head())

    print("\nPlayer counts by position:")
    print(rosters_df["position"].value_counts())

if __name__ == "__main__":
    main()
