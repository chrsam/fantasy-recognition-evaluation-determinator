
from collections import Counter
from src.espn_connection import connect_to_league

def collect_free_agents():

    league = connect_to_league()

    print("===== ESPN FREE AGENT RETRIEVAL =====")

    # Retrieve up to 50 available free agents
    free_agents = league.free_agents(size=50)

    print(f"\nFree agents retrieved: {len(free_agents)}")

    # Display position breakdown
    positions = [
        getattr(player, "position", "Unknown")
        for player in free_agents
    ]

    print("\nPlayers by position:")
    print(Counter(positions))

    # Inspect the first player's available attributes
    if free_agents:
        sample_player = free_agents[0]
        print("\n===== PLAYER ATTRIBUTE INSPECTION =====")
        print(f"Player type: {type(sample_player)}")
        attributes = [
            attribute
            for attribute in dir(sample_player)
            if not attribute.startswith("_")
        ]
        print("\nAvailable attributes:")
        print(attributes)
        print("\nSample player information:")
        for attribute in [
            "name",
            "playerId",
            "position",
            "proTeam",
            "total_points",
            "avg_points",
            "projected_points",
            "injuryStatus"
        ]:
            if hasattr(sample_player, attribute):
                print(
                    f"{attribute}: "
                    f"{getattr(sample_player, attribute)}"
                )
        print("\n===== FIRST 10 FREE AGENTS =====")
        for player in free_agents[:10]:
            print(
                f"{player.name} | "
                f"{player.position} | "
                f"{player.proTeam}"
            )

if __name__ == "__main__":
    collect_free_agents()    
