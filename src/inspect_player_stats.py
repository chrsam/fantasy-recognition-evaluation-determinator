
from src.espn_connection import connect_to_league

def inspect_player_stats():

    league = connect_to_league()

    # Get one rostered player
    roster_player = league.teams[0].roster[0]

    # Get one free agent
    free_agent = league.free_agents(size=1)[0]

    players = [
        ("ROSTERED PLAYER", roster_player),
        ("FREE AGENT", free_agent)
    ]

    for label, player in players:
        print(f"\n===== {label} =====")
        print(f"Name: {player.name}")

        print("\n===== PLAYER STATS =====")
        if hasattr(player, "stats"):
            for week, stats in player.stats.items():
                print(f"\nWeek: {week}")
                print(f"Stats: {stats}")
        else:
            print("No weekly statistics available.")

if __name__ == "__main__":
    inspect_player_stats()
