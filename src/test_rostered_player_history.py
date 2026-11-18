
from src.espn_connection import connect_to_league

def test_rostered_player_history():
    league = connect_to_league()

    # Choose a rostered player from the league.
    player = league.teams[0].roster[0]

    print("===== ROSTERED PLAYER =====")
    print(f"Player: {player.name}")
    print(f"Player ID: {player.playerId}")
    print(f"Roster stats keys: {list(player.stats.keys())}")

    # Retrieve the same player using player_info().
    detailed_player = league.player_info(
        playerId=player.playerId
    )

    print("\n===== PLAYER INFO RESULT =====")
    print(f"Player: {detailed_player.name}")
    print(f"Stats keys: {list(detailed_player.stats.keys())}")

    for week in range(6, 11):

        stats = detailed_player.stats.get(week, {})

        print(
            f"Week {week}: "
            f"{stats.get('points', 'NOT AVAILABLE')}"
        )

if __name__ == "__main__":
    test_rostered_player_history()
