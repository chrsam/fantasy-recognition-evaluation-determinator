
from src.espn_connection import connect_to_league

def test_batch_player_history():
    league = connect_to_league()

    # Choose 3 rostered players from the league.
    players = league.teams[0].roster[:3]
    player_ids = [player.playerId for player in players]

    print("===== BATCH PLAYER LOOKUP =====")
    print(f"Requested player IDs: {player_ids}")

    results = league.player_info(playerId=player_ids)
    print(f"Returned object type: {type(results)}")

    if not isinstance(results, list):
        results = [results]

    print(f"Players returned: {len(results)}")

    for player in results:
        print(f"\nPlayer: {player.name}")
        print(f"Player ID: {player.playerId}")

        actual_weeks = sorted(
            int(week)
            for week, stats in player.stats.items()
            if(
                str(week).isdigit()
                and int(week) > 0
                and isinstance(stats, dict)
                and stats.get("points") is not None
            )
        )

        print(f"Weeks with actual scores: {actual_weeks}")

if __name__ == "__main__":
    test_batch_player_history()
