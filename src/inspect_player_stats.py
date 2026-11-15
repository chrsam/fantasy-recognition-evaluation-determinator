
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

        for attribute in dir(player):
            if any(
                keyword in attribute.lower()
                for keyword in [
                    "game",
                    "point",
                    "project",
                    "stat",
                    "injur"
                ]
            ):
                if not attribute.startswith("_"):
                    try:
                        value = getattr(player, attribute)
                        if not callable(value):
                            print(f"{attribute}: {value}")
                    except Exception:
                        pass

if __name__ == "__main__":
    inspect_player_stats()
