
import pandas as pd
from pathlib import Path
from src.espn_connection import connect_to_league

# Locate database
BASE_DIR = Path(__file__).resolve().parent.parent


def collect_free_agents():

    league = connect_to_league()

    print("===== COLLECTING ESPN FREE AGENTS =====")

    # Retrieve up to 100 available free agents
    free_agents = league.free_agents(size=100)

    print(f"\nFree agents retrieved: {len(free_agents)}")

    # Convert player objects into dictionaries
    player_data = []
    for player in free_agents:
        player_data.append({
            "player_id": player.playerId,
            "player_name": player.name,
            "position": player.position,
            "nfl_team": player.proTeam,
            "total_points": player.total_points,
            "average_points": player.avg_points,
            "projected_points": player.projected_total_points,
            "projected_avg_points": player.projected_avg_points,
            "projected_total_points": player.projected_total_points,
            "injury_status": player.injuryStatus,
            "percent_owned": player.percent_owned,
            "percent_started": player.percent_started,
            "on_team_id": player.onTeamId
        })

    # Create DataFrame
    df = pd.DataFrame(player_data)

    # Remove duplicate player IDs, if any
    df = df.drop_duplicates(
        subset=["player_id"]
    )

    # Save free-agent data
    output_path = BASE_DIR / "data" / "free_agents.csv"

    df.to_csv(
        output_path,
        index=False
    )

    print("\n===== FREE AGENT SUMMARY =====")
    print(f"Unique players collected: {len(df)}")

    print("\nPlayers by position:")
    print(df["position"].value_counts().to_string())

    print("\nPlayers with an assigned fantasy team:")
    print((df["on_team_id"] != 0).sum())

    print("\nSaved file:")
    print(output_path)

if __name__ == "__main__":
    collect_free_agents()    
