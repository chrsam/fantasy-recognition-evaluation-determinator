
from src.espn_connection import connect_to_league

def test_position_filters():

    league = connect_to_league()   

    positions = ["QB", "RB", "WR", "TE"]

    print("===== TESTING POSITION FILTERS =====")

    for position in positions:
        players = league.free_agents(
            size=100,
            position=position
        )

        print(f"\nRequested position: {position}")
        print(f"Players returned: {len(players)}")

        actual_positions = {
            player.position for player in players
        }

        print(f"Positions returned: {actual_positions}")

if __name__ == "__main__":
    test_position_filters()
